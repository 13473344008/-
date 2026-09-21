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
	return previewJPEG(source, mime, MaxSourceBytes, 480, 75, 256*1024)
}

// DisplayPreviewJPEG derives a screen-sized image from a verified frozen PNG.
// It does not replace the source bytes or their publication hash.
func DisplayPreviewJPEG(source []byte) ([]byte, error) {
	return previewJPEG(source, "image/png", MaxNormalizedBytes, 1200, 85, 2*1024*1024)
}

func previewJPEG(source []byte, mime string, maxBytes, edge, quality, maxOutput int) ([]byte, error) {
	if len(source) == 0 || len(source) > maxBytes {
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
	if w > edge || h > edge {
		if w >= h {
			h, w = max(1, h*edge/w), edge
		} else {
			w, h = max(1, w*edge/h), edge
		}
	}
	dst := image.NewRGBA(image.Rect(0, 0, w, h))
	draw.Draw(dst, dst.Bounds(), image.NewUniform(color.White), image.Point{}, draw.Src)
	xdraw.ApproxBiLinear.Scale(dst, dst.Bounds(), im, im.Bounds(), draw.Over, nil)
	var out bytes.Buffer
	if err = jpeg.Encode(&out, dst, &jpeg.Options{Quality: quality}); err != nil {
		return nil, err
	}
	if out.Len() > maxOutput {
		return nil, fmt.Errorf("preview size")
	}
	return out.Bytes(), nil
}
