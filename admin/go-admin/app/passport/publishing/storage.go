package publishing

import (
	"fmt"
	"github.com/google/uuid"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"
)

type Store struct{ Public, Work *os.Root }

func OpenStore(public, work string) (*Store, error) {
	if !filepath.IsAbs(public) || !filepath.IsAbs(work) {
		return nil, fmt.Errorf("storage paths must be absolute")
	}
	p, e := filepath.EvalSymlinks(public)
	if e != nil {
		return nil, e
	}
	w, e := filepath.EvalSymlinks(work)
	if e != nil {
		return nil, e
	}
	if p != filepath.Clean(public) || w != filepath.Clean(work) || p == w || strings.HasPrefix(w, p+"/") || strings.HasPrefix(p, w+"/") {
		return nil, fmt.Errorf("public and private roots must be separate, without symlinks")
	}
	pi, e := os.Stat(p)
	if e != nil {
		return nil, e
	}
	wi, e := os.Stat(w)
	if e != nil {
		return nil, e
	}
	if pi.Sys().(*syscall.Stat_t).Dev != wi.Sys().(*syscall.Stat_t).Dev {
		return nil, fmt.Errorf("roots must share filesystem")
	}
	pr, e := os.OpenRoot(p)
	if e != nil {
		return nil, e
	}
	wr, e := os.OpenRoot(w)
	if e != nil {
		pr.Close()
		return nil, e
	}
	s := &Store{pr, wr}
	for _, dir := range []string{"locks", "tmp", "manifests"} {
		if e = wr.MkdirAll(dir, 0700); e != nil {
			s.Close()
			return nil, e
		}
	}
	for _, dir := range []string{"published", "versions", "assets/sha256"} {
		if e = pr.MkdirAll(dir, 0755); e != nil {
			s.Close()
			return nil, e
		}
	}
	return s, nil
}
func (s *Store) Close() { s.Public.Close(); s.Work.Close() }
func (s *Store) Lock(id string) (func(), error) {
	if _, e := uuid.Parse(id); e != nil {
		return nil, fmt.Errorf("invalid batch identity")
	}
	f, e := s.Work.OpenFile("locks/"+id+".lock", os.O_CREATE|os.O_RDWR, 0600)
	if e != nil {
		return nil, e
	}
	if e = syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); e != nil {
		f.Close()
		return nil, fmt.Errorf("batch publish lock busy")
	}
	return func() { syscall.Flock(int(f.Fd()), syscall.LOCK_UN); f.Close() }, nil
}
func syncDir(r *os.Root, dir string) error {
	f, e := r.Open(dir)
	if e != nil {
		return e
	}
	defer f.Close()
	return f.Sync()
}
func checkedDir(r *os.Root, name string, mode os.FileMode) error {
	if path.Clean(name) != name || strings.Contains(name, "..") || strings.HasPrefix(name, "/") {
		return fmt.Errorf("unsafe directory")
	}
	if e := r.MkdirAll(name, mode); e != nil {
		return e
	}
	parts := strings.Split(name, "/")
	for i := range parts {
		st, e := r.Lstat(strings.Join(parts[:i+1], "/"))
		if e != nil {
			return e
		}
		if !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
			return fmt.Errorf("unsafe directory component")
		}
	}
	return nil
}

// Immutable writes install a complete fsynced temporary file using an atomic no-replace hard link.
// Existing content is reusable only after byte-hash verification; partial copies never occupy CAS names.
func Immutable(r *os.Root, name string, data []byte, mode os.FileMode) error {
	dir := path.Dir(name)
	if e := checkedDir(r, dir, 0755); e != nil {
		return e
	}
	if old, e := ReadRegular(r, name, int64(len(data))+1); e == nil {
		if len(old) != len(data) || Hash(old) != Hash(data) {
			return fmt.Errorf("immutable content conflict")
		}
		return nil
	} else if !os.IsNotExist(e) {
		return e
	}
	tmp := dir + "/.write-" + uuid.NewString()
	f, e := r.OpenFile(tmp, os.O_CREATE|os.O_EXCL|os.O_WRONLY, mode)
	if e != nil {
		return e
	}
	defer r.Remove(tmp)
	if _, e = f.Write(data); e != nil {
		f.Close()
		return e
	}
	if e = f.Sync(); e != nil {
		f.Close()
		return e
	}
	if e = f.Close(); e != nil {
		return e
	}
	if e = r.Link(tmp, name); e != nil {
		if !os.IsExist(e) {
			return e
		}
		old, err := ReadRegular(r, name, int64(len(data))+1)
		if err != nil || Hash(old) != Hash(data) {
			return fmt.Errorf("immutable content conflict")
		}
	}
	return syncDir(r, dir)
}
func (s *Store) Current(code string) ([]byte, error) {
	if !regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`).MatchString(code) {
		return nil, fmt.Errorf("unsafe batch code")
	}
	return ReadRegular(s.Public, "published/"+code+".json", MaxPayloadBytes)
}

// Switch is the sole public head mutation. An error after rename means an uncertain commit, never a safe retry.
func (s *Store) Switch(code string, data []byte) (renamed bool, err error) {
	if !regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`).MatchString(code) {
		return false, fmt.Errorf("unsafe batch code")
	}
	if e := checkedDir(s.Public, "published", 0755); e != nil {
		return false, e
	}
	name := "published/" + code + ".json"
	tmp := "published/.switch-" + uuid.NewString()
	f, e := s.Public.OpenFile(tmp, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	if e != nil {
		return false, e
	}
	defer s.Public.Remove(tmp)
	if _, e = f.Write(data); e != nil {
		f.Close()
		return false, e
	}
	if e = f.Sync(); e != nil {
		f.Close()
		return false, e
	}
	if e = f.Close(); e != nil {
		return false, e
	}
	if e = s.Public.Rename(tmp, name); e != nil {
		return false, e
	}
	return true, syncDir(s.Public, "published")
}
