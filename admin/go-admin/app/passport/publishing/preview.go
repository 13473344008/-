package publishing

import (
	"bytes"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/jpeg"

	xdraw "golang.org/x/image/draw"
)

// PreviewJPEG is display-only: it never changes stored originals or publication hashes.
func PreviewJPEG(source []byte, mime string) ([]byte, error) {
	if len(source) == 0 || len(source) > MaxSourceBytes {
		return nil, fmt.Errorf("source size")
	}
	cfg, format, err := image.DecodeConfig(bytes.NewReader(source))
	if err != nil || (format != "jpeg" && format != "png") || mime != "image/"+format {
		return nil, fmt.Errorf("invalid preview image")
	}
	if cfg.Width <= 0 || cfg.Height <= 0 || cfg.Width > 4096 || cfg.Height > 4096 || int64(cfg.Width)*int64(cfg.Height) > 16000000 {
		return nil, fmt.Errorf("pixel limit")
	}
	im, _, err := image.Decode(bytes.NewReader(source))
	if err != nil {
		return nil, err
	}
	w, h := cfg.Width, cfg.Height
	if w > 480 || h > 480 {
		if w >= h {
			h, w = max(1, h*480/w), 480
		} else {
			w, h = max(1, w*480/h), 480
		}
	}
	dst := image.NewRGBA(image.Rect(0, 0, w, h))
	draw.Draw(dst, dst.Bounds(), image.NewUniform(color.White), image.Point{}, draw.Src)
	xdraw.ApproxBiLinear.Scale(dst, dst.Bounds(), im, im.Bounds(), draw.Over, nil)
	var out bytes.Buffer
	if err = jpeg.Encode(&out, dst, &jpeg.Options{Quality: 75}); err != nil {
		return nil, err
	}
	if out.Len() > 256*1024 {
		return nil, fmt.Errorf("preview size")
	}
	return out.Bytes(), nil
}
