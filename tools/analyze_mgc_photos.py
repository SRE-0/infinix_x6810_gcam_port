"""Compare repeat JPEG captures using EXIF and user-selected fixed ROIs.

Metrics measure image high frequencies, not optical resolution or calibrated noise.
Use a fixed camera, scene, focus and illumination; avoid moving foliage/displays.
Requires numpy and Pillow (scripts/requirements-photo.txt).
"""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps


def inspect(path, rois):
    with Image.open(path) as source:
        exif = source.getexif().get_ifd(34665)
        image = ImageOps.exif_transpose(source).convert('RGB')
    arr = np.asarray(image, dtype=float) / 255
    row = {'file': path.name, 'size': image.size, 'iso': exif.get(34855),
           'exposure_s': float(exif.get(33434, 0)),
           'focal_mm': float(exif.get(37386, 0)), 'rois': {}}
    for name, (x1, y1, x2, y2) in rois.items():
        if not (0 <= x1 < x2 <= image.width and 0 <= y1 < y2 <= image.height) or min(x2-x1,y2-y1)<3:
            raise ValueError(f'Invalid ROI for {path.name}: {name}')
        a = arr[y1:y2, x1:x2]
        y = a @ np.array([.2126, .7152, .0722])
        lap = y[1:-1,:-2]+y[1:-1,2:]+y[:-2,1:-1]+y[2:,1:-1]-4*y[1:-1,1:-1]
        rb, bb = a[:,:,0]-a[:,:,1], a[:,:,2]-a[:,:,1]
        row['rois'][name] = {
            'mean_rgb': a.mean(axis=(0,1)).tolist(), 'mean_luma': float(y.mean()),
            'gradient_rms': float(np.sqrt((np.diff(y,axis=0)**2).mean()+(np.diff(y,axis=1)**2).mean())),
            'laplacian_std': float(lap.std()),
            'chroma_gradient': float(np.sqrt((np.diff(rb,axis=1)**2).mean()+(np.diff(bb,axis=1)**2).mean())),
            'clip_fraction': float((a.max(axis=2)>=254/255).mean())}
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, nargs='+', required=True)
    parser.add_argument('--candidate', type=Path, nargs='+', required=True)
    parser.add_argument('--roi', action='append', required=True, help='NAME:X1,Y1,X2,Y2 in upright image pixels')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rois = {}
    for item in args.roi:
        name, coordinates = item.split(':',1)
        values = tuple(map(int, coordinates.split(',')))
        if not name or name in rois or len(values)!=4:
            parser.error('ROIs need unique names and four coordinates')
        rois[name] = values
    groups = {label:[inspect(p,rois) for p in paths] for label,paths in
              [('baseline',args.baseline),('candidate',args.candidate)]}
    rows = groups['baseline']+groups['candidate']
    issues = []
    if len({tuple(r['size']) for r in rows})>1 or len({r['focal_mm'] for r in rows})>1:
        issues.append('Different dimensions or focal lengths: comparisons are invalid')
    for key in ('iso','exposure_s'):
        values = [r[key] for r in rows]
        if not all(v and v>0 for v in values):
            issues.append(f'Missing or invalid {key}')
        elif max(values)/min(values)>1.1:
            issues.append(f'{key} varies by more than 10%: exposure is a confounder')
    metrics = ('mean_luma','gradient_rms','laplacian_std','chroma_gradient','clip_fraction')
    summaries = {label:{name:{metric:{'median':float(np.median([r['rois'][name][metric] for r in entries])),
                                      'min':float(min(r['rois'][name][metric] for r in entries)),
                                      'max':float(max(r['rois'][name][metric] for r in entries))}
                                    for metric in metrics} for name in rois}
                 for label,entries in groups.items()}
    result = {'images':groups,'summaries':summaries,'confounders':issues,
              'limitations':'No registration, focus measurement, color target or noise calibration. Higher gradients may be noise or sharpening; clipping is JPEG output, not RAW dynamic range.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'images':len(rows),'confounders':issues,'output':str(args.output)},indent=2))


if __name__ == '__main__':
    main()
