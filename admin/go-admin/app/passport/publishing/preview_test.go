package publishing

import (
	"bytes"
	"image"
	"image/color"
	"image/jpeg"
	"image/png"
	"testing"
)

func TestPreviewIsBoundedAndPreservesSource(t *testing.T) {
	im := image.NewRGBA(image.Rect(0, 0, 1600, 900))
	for y := 0; y < 900; y++ {
		for x := 0; x < 1600; x++ {
			im.SetRGBA(x, y, color.RGBA{uint8(x*31 + y*7), uint8(x*3 + y*13), uint8(x + y*5), 255})
		}
	}
	var src bytes.Buffer
	if err := jpeg.Encode(&src, im, &jpeg.Options{Quality: 85}); err != nil {
		t.Fatal(err)
	}
	before := bytes.Clone(src.Bytes())
	p, err := PreviewJPEG(src.Bytes(), "image/jpeg")
	if err != nil {
		t.Fatal(err)
	}
	cfg, format, err := image.DecodeConfig(bytes.NewReader(p))
	if err != nil || format != "jpeg" || cfg.Width != 480 || cfg.Height != 270 {
		t.Fatalf("invalid preview: %+v %s %v", cfg, format, err)
	}
	if len(p) >= len(before)/3 || len(p) > 256*1024 {
		t.Fatalf("preview too large: %d, source %d", len(p), len(before))
	}
	if !bytes.Equal(before, src.Bytes()) {
		t.Fatal("original modified")
	}
	if _, err = PreviewJPEG(before, "image/png"); err == nil {
		t.Fatal("MIME mismatch accepted")
	}
}

func TestPreviewTransparencyAndInvalidInput(t *testing.T) {
	var b bytes.Buffer
	if err := png.Encode(&b, image.NewNRGBA(image.Rect(0, 0, 8, 4))); err != nil {
		t.Fatal(err)
	}
	p, err := PreviewJPEG(b.Bytes(), "image/png")
	if err != nil {
		t.Fatal(err)
	}
	im, err := jpeg.Decode(bytes.NewReader(p))
	if err != nil {
		t.Fatal(err)
	}
	r, g, bl, _ := im.At(0, 0).RGBA()
	if r < 65000 || g < 65000 || bl < 65000 {
		t.Fatal("transparent area not white")
	}
	for _, input := range [][]byte{nil, []byte("not an image"), make([]byte, MaxSourceBytes+1)} {
		if _, err := PreviewJPEG(input, "image/png"); err == nil {
			t.Fatal("invalid source accepted")
		}
	}
}
