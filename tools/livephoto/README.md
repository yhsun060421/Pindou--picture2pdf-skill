# Live Photo demo

`cover.jpg` + `clip.mov` are derived from `assets/preview.gif`:

- `cover.jpg` — 900×878 key frame (the overview page)
- `clip.mov` — 2.8 s H.264 slideshow at 15 fps

A real Apple Live Photo needs Apple-specific metadata (MakerNote tag 17 on the
image and `com.apple.quicktime.content.identifier` on the movie). That metadata
is easiest to write on macOS with [makelive](https://github.com/RhetTbull/makelive).

Run the **make-live-photo** GitHub Actions workflow (macOS runner) to produce:

- `cover.pvt/` — a Live Photo package that imports into Photos with a double-click
- `cover.jpg` + `clip.mov` — the pair with matching ContentIdentifier metadata

Local macOS equivalent:

```bash
uvx makelive -p --manual cover.jpg clip.mov   # creates cover.pvt
uvx makelive --manual cover.jpg clip.mov      # metadata in the pair
```

## Import on Apple devices

- **Mac**: double-click `cover.pvt` → Photos imports it as a Live Photo. It then
  syncs to iPhone/iPad through iCloud Photos.
- **iPhone/iPad only**: use an app such as *intoLive* or *Live Photo Converter*
  with `clip.mov` as the source.
