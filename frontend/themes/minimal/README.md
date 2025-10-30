# Minimal Theme

A clean, minimalist theme for MyCMS with essential styling and responsive design.

## Features

- ✨ Clean and simple design
- 📱 Fully responsive (mobile, tablet, desktop)
- ⚡ Fast loading with minimal CSS
- 🎨 Easy to customize
- ♿ Accessible markup

## Installation

The Minimal theme comes bundled with MyCMS. To activate it:

```python
from mycms.frontend.themes import get_theme_manager

theme_manager = get_theme_manager()
theme_manager.register_theme_from_config(
    "mycms/frontend/themes/minimal/theme.json"
)
theme_manager.activate_theme("minimal")
```

## Color Palette

- **Primary**: #3498db (Blue)
- **Secondary**: #2c3e50 (Dark Blue-Gray)
- **Background**: #ffffff (White)
- **Text**: #333333 (Dark Gray)

## Templates Included

- `home.html` - Homepage template
- `page.html` - Static page template
- `post.html` - Blog post template

## Customization

To customize the theme, you can:

1. **Copy the theme** to create your own variant:
```bash
cp -r mycms/frontend/themes/minimal mycms/frontend/themes/my-theme
```

2. **Edit theme.json** to change metadata and colors

3. **Modify templates** to change layout and styling

4. **Register your custom theme**:
```python
theme_manager.register_theme_from_config(
    "mycms/frontend/themes/my-theme/theme.json"
)
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

MIT License - Part of MyCMS
