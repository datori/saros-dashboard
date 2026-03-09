## 1. HTML Head — PWA Meta Tags

- [x] 1.1 Add `viewport-fit=cover` to the existing `<meta name="viewport">` tag in `_HTML`
- [x] 1.2 Add `<meta name="apple-mobile-web-app-capable" content="yes">` to `_HTML` `<head>`
- [x] 1.3 Add `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">` to `_HTML` `<head>`
- [x] 1.4 Add `<meta name="apple-mobile-web-app-title" content="Vacuum">` to `_HTML` `<head>`
- [x] 1.5 Add `<meta name="theme-color" content="#22272e">` to `_HTML` `<head>`
- [x] 1.6 Add `<link rel="manifest" href="/manifest.json">` to `_HTML` `<head>`
- [x] 1.7 Add `<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">` to `_HTML` `<head>`

## 2. Safe-Area CSS

- [x] 2.1 Update `body` CSS in `_HTML` to use `padding: max(20px, env(safe-area-inset-top)) max(20px, env(safe-area-inset-right)) max(20px, env(safe-area-inset-bottom)) max(20px, env(safe-area-inset-left))`

## 3. Icon Route

- [x] 3.1 Add `GET /icons/apple-touch-icon.png` FastAPI route in `dashboard.py` that returns an SVG response with `Content-Type: image/svg+xml` — dark circle (`#22272e`) with white stylized vacuum/robot mark

## 4. Manifest Route

- [x] 4.1 Add `GET /manifest.json` FastAPI route in `dashboard.py` that returns `JSONResponse` with `name`, `short_name`, `start_url`, `display`, `background_color`, `theme_color`, and `icons` array referencing `/icons/apple-touch-icon.png`
