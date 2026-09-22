package publishing

import (
	"bytes"
	"image"
	"image/jpeg"
	"image/png"
	"math/rand"
	"os"
	"testing"
)

func TestJPEGUploadLimitIsSeparateFromNormalizedPNG(t *testing.T) {
	im := image.NewNRGBA(image.Rect(0, 0, 1200, 900))
	r := rand.New(rand.NewSource(1))
	for i := 0; i < len(im.Pix); i += 4 {
		im.Pix[i], im.Pix[i+1], im.Pix[i+2], im.Pix[i+3] = byte(r.Intn(256)), byte(r.Intn(256)), byte(r.Intn(256)), 255
	}
	var source bytes.Buffer
	if e := jpeg.Encode(&source, im, &jpeg.Options{Quality: 80}); e != nil {
		t.Fatal(e)
	}
	if source.Len() >= MaxSourceBytes {
		t.Fatal("fixture exceeds upload limit")
	}
	normalized, e := Normalize(source.Bytes(), "image/jpeg")
	if e != nil {
		t.Fatal(e)
	}
	if len(normalized) <= MaxSourceBytes {
		t.Fatal("fixture must exercise PNG expansion")
	}
	decoded, e := png.Decode(bytes.NewReader(normalized))
	if e != nil || decoded.Bounds() != im.Bounds() {
		t.Fatal("dimensions changed", e)
	}
	root, e := os.OpenRoot(t.TempDir())
	if e != nil {
		t.Fatal(e)
	}
	defer root.Close()
	if e = Immutable(root, "image.png", normalized, 0644); e != nil {
		t.Fatal(e)
	}
	stored, e := ReadRegular(root, "image.png", MaxNormalizedBytes)
	if e != nil || Hash(stored) != Hash(normalized) {
		t.Fatal("published image readback failed", e)
	}
}
