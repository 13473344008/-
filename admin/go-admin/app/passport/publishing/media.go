package publishing

import (
	"bytes"
	"fmt"
	"image"
	_ "image/jpeg"
	"image/png"
	"io"
	"os"
	"path"
	"strings"
)

const TransformVersion = "image-png-v1-go1.26"
const MaxSourceBytes = 2 * 1024 * 1024

// ReadPrivate refuses symlinks and non-regular files; the Root also confines lookup against traversal.
func ReadPrivate(rootDir, key string) ([]byte, error) {
	r, e := os.OpenRoot(rootDir)
	if e != nil {
		return nil, e
	}
	defer r.Close()
	return ReadRegular(r, key, MaxSourceBytes)
}
func ReadRegular(r *os.Root, key string, limit int64) ([]byte, error) {
	if key == "" || path.Clean(key) != key || strings.HasPrefix(key, "/") || strings.ContainsAny(key, "\\:\x00") {
		return nil, fmt.Errorf("unsafe relative path")
	}
	parts := strings.Split(key, "/")
	for i, p := range parts {
		if p == ".." || p == "." {
			return nil, fmt.Errorf("unsafe component")
		}
		info, e := r.Lstat(strings.Join(parts[:i+1], "/"))
		if e != nil {
			return nil, e
		}
		if info.Mode()&os.ModeSymlink != 0 {
			return nil, fmt.Errorf("symlinks forbidden")
		}
	}
	f, e := r.Open(key)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	st, e := f.Stat()
	if e != nil {
		return nil, e
	}
	if !st.Mode().IsRegular() || st.Size() < 1 || st.Size() > limit {
		return nil, fmt.Errorf("file type/size rejected")
	}
	b, e := io.ReadAll(io.LimitReader(f, limit+1))
	if int64(len(b)) > limit {
		return nil, fmt.Errorf("file too large")
	}
	return b, e
}

// Normalize decodes bounded JPEG/PNG pixels and re-encodes a metadata-free PNG. SVG/PDF are fail-closed.
func Normalize(source []byte, mime string) ([]byte, error) {
	if len(source) == 0 || len(source) > MaxSourceBytes {
		return nil, fmt.Errorf("source size")
	}
	cfg, format, e := image.DecodeConfig(bytes.NewReader(source))
	if e != nil {
		return nil, fmt.Errorf("invalid image")
	}
	if mime != "image/"+format || format != "jpeg" && format != "png" {
		return nil, fmt.Errorf("unsupported image MIME")
	}
	if cfg.Width <= 0 || cfg.Height <= 0 || cfg.Width > 4096 || cfg.Height > 4096 || int64(cfg.Width)*int64(cfg.Height) > 16000000 {
		return nil, fmt.Errorf("pixel limit")
	}
	im, _, e := image.Decode(bytes.NewReader(source))
	if e != nil {
		return nil, e
	}
	var out bytes.Buffer
	if e = png.Encode(&out, im); e != nil {
		return nil, e
	}
	if out.Len() > MaxSourceBytes {
		return nil, fmt.Errorf("normalized image too large")
	}
	return out.Bytes(), nil
}
