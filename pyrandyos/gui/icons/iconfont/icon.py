# The MIT License
#
# Copyright (c) 2015 The Spyder development team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from typing import TYPE_CHECKING
from importlib import import_module
from weakref import WeakValueDictionary

from ....logging import log_func_call, DEBUGLOW2  # noqa: E402
from ....utils.hash import TupleHashMixin  # noqa: E402
from ...gui_app import get_gui_app
from ...qt import (
    QRect, Qt, QSizeF, QRectF, QPointF, QSize, QPoint, QPainter, QColor,
    QTransform, QFont, QRawFont, QImage, QIcon, QIconEngine, QPixmap, QPalette,
    QGlyphRun,
)
from ...utils import painter_context  # noqa: E402
from .animation import IconAnimation  # noqa: E402
from .sources import THIRDPARTY_FONTSPEC  # noqa: E402
if TYPE_CHECKING:
    from .font import IconFont

_NOHINT = QFont.PreferNoHinting
_DEFHINT = QFont.PreferDefaultHinting

IconCache = WeakValueDictionary[str, QIcon]
PaletteType = QPalette.ColorRole | tuple[QPalette.ColorGroup,
                                         QPalette.ColorRole]
RgbTriple = tuple[int, int, int]
RgbaQuad = tuple[int, int, int, int]
ColorType = str | QColor | PaletteType | RgbTriple | RgbaQuad


class IconLayer(TupleHashMixin):
    def as_tuple(self):
        anim = self.animation
        return (
            self.font._SPECNAME,
            self.glyph,
            self._orig_color,
            self.x,
            self.y,
            anim.as_tuple() if anim else None,
            self.scale,
            self.opacity,
            self.rotation,
            self.hflip,
            self.vflip,
            self.draw,
            self._alpha,
            self._is_disabled_icon,
        )

    @log_func_call(DEBUGLOW2, trace_only=True)
    def __init__(
        self,
        font: 'IconFont | type[IconFont] | str',
        glyph: str | int = None,
        color: ColorType = None,
        x: int = 0,
        y: int = 0,
        animation: IconAnimation | tuple = None,
        scale: float = 1.0,
        opacity: float = 1.0,
        rotation: float = 0.0,
        hflip: bool = False,
        vflip: bool = False,
        draw: str = None,

        # these are only used to precompute color:
        alpha: int = None,
        is_disabled_icon: bool = False,

        *,
        glyph_name: str = None,  # not saved, just used to set glyph
    ):
        if isinstance(font, str):
            font = THIRDPARTY_FONTSPEC[font].get_font_class()

        self.font = font
        if glyph and glyph_name:
            raise ValueError(
                "Cannot specify both 'glyph' and 'glyph_name'. "
                "Use 'glyph_name' to set the glyph from the font's charmap."
            )
        if not glyph:
            if glyph_name:
                glyph = font.get_codepoint_by_name(glyph_name)
                if not glyph:
                    raise ValueError(
                        f"Glyph name '{glyph_name}' not found in "
                        f"font {font._SPECNAME}."
                    )
            else:
                raise ValueError(
                    "Either 'glyph' or 'glyph_name' must be specified."
                )
        self.glyph = glyph if isinstance(glyph, str) else chr(glyph)

        self._orig_color = color
        if not color:
            color = ((QPalette.Disabled, QPalette.WindowText)
                     if is_disabled_icon else QPalette.WindowText)

        if not self.is_palette_color(color) and not isinstance(color, QColor):
            color = QColor(color) if isinstance(color, str) else QColor(*color)

        self.color = color
        self.x = x
        self.y = y

        if isinstance(animation, tuple):
            qualname: str = animation[0]
            qualnameparts = qualname.split('.')
            mod = import_module(qualnameparts[:-1])
            animation = getattr(mod, qualnameparts[-1])(*animation[1:])

        self.animation = animation
        self.scale = scale
        self.opacity = opacity
        self.rotation = rotation
        self.hflip = hflip
        self.vflip = vflip
        self.draw = draw or ('path' if animation else 'text')
        self._alpha = alpha
        self._is_disabled_icon = is_disabled_icon

    @staticmethod
    def is_palette_color(color: ColorType):
        return (isinstance(color, QPalette.ColorRole) or
                (isinstance(color, tuple)
                 and isinstance(color[0], QPalette.ColorGroup)
                 and isinstance(color[1], QPalette.ColorRole)))

    def get_color(self):
        color = self.color
        if self.is_palette_color(color):
            app = get_gui_app()
            if app:
                palette = app.qtobj.palette()
                color = palette.color(*(color if isinstance(color, tuple)
                                        else (color,)))
            else:
                color = (QColor(150, 150, 150) if self._is_disabled_icon
                         else QColor(50, 50, 50))

        alpha = self._alpha
        if alpha:
            color.setAlpha(alpha)

        return color

    def paint(self, painter: QPainter, rect: QRect):
        font = self.font
        with painter_context(painter):
            painter.setPen(self.get_color())

            anim = self.animation
            if anim:
                anim.setup(font, painter, rect)

            rect = QRect(rect)
            rect.translate(self.x*rect.width(), self.y*rect.height())
            x_center = rect.width() * 0.5
            y_center = rect.height() * 0.5
            transform = QTransform()
            transform.translate(x_center, y_center)
            if self.vflip:
                transform.scale(1, -1)

            if self.hflip:
                transform.scale(-1, 1)

            rotate = self.rotation
            if rotate:
                transform.rotate(rotate)

            transform.translate(-x_center, -y_center)
            painter.setTransform(transform)

            painter.setOpacity(self.opacity)
            draw = self.draw
            rawfont = self.get_rawfont(rect) if draw != 'text' else None
            done = False
            if rawfont:
                if draw == 'path':
                    done = self.draw_path(painter, rect, rawfont)

                elif draw == 'glyphrun':
                    done = self.draw_glyphrun(painter, rect, rawfont)

                elif draw == 'image':
                    done = self.draw_image(painter, rect, rawfont)

            if draw == 'text' or not done:
                done = self.draw_text(painter, rect)

    def get_draw_size(self, rect: QRect):
        # A 16 pixel-high icon yields a font size of 14, which is pixel
        # perfect for font-awesome. 16 * 0.875 = 14
        # The reason why the glyph size is smaller than the icon size is to
        # account for font bearing.
        return round(0.875*rect.height()*self.scale)

    def draw_text(self, painter: QPainter, rect: QRect):
        font = self.font.get_font(self.get_draw_size(rect))
        if self.animation:
            font.setHintingPreference(_NOHINT)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter, self.glyph)
        return True

    def get_rawfont(self, rect: QRect):
        hint = (_NOHINT if (self.animation and self.draw == "glyphrun")
                else _DEFHINT)
        rawfont = self.font.get_rawfont(self.get_draw_size(rect), hint)
        if rawfont.fontTable("glyf"):
            return rawfont

    def prep_rawfont_paint(self, painter: QPainter, rect: QRect,
                           rawfont: QRawFont):
        glyph = rawfont.glyphIndexesForString(self.glyph)[0]
        advance = rawfont.advancesForGlyphIndexes((glyph,))[0]
        ascent = rawfont.ascent()
        size = QSizeF(abs(advance.x()), ascent + rawfont.descent())
        painter.translate(QRectF(rect).center())
        painter.translate(-size.width() / 2, -size.height() / 2)
        return glyph, ascent

    def draw_path(self, painter: QPainter, rect: QRect, rawfont: QRawFont):
        glyph, ascent = self.prep_rawfont_paint(painter, rect, rawfont)
        path = rawfont.pathForGlyph(glyph)
        path.translate(0, ascent)
        path.setFillRule(Qt.WindingFill)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillPath(path, painter.pen().color())
        return True

    def draw_glyphrun(self, painter: QPainter, rect: QRect, rawfont: QRawFont):
        if not QGlyphRun:
            return False

        glyph, ascent = self.prep_rawfont_paint(painter, rect, rawfont)
        glyphrun = QGlyphRun()
        glyphrun.setRawFont(rawfont)
        glyphrun.setGlyphIndexes((glyph,))
        glyphrun.setPositions((QPointF(0, ascent),))
        painter.drawGlyphRun(QPointF(0, 0), glyphrun)
        return True

    def draw_image(self, painter: QPainter, rect: QRect, rawfont: QRawFont):
        glyph, ascent = self.prep_rawfont_paint(painter, rect, rawfont)
        image = rawfont.alphaMapForGlyph(
            glyph, QRawFont.PixelAntialiasing
        ).convertToFormat(QImage.Format_ARGB32_Premultiplied)
        painter2 = QPainter(image)
        painter2.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter2.fillRect(image.rect(), painter.pen().color())
        painter2.end()
        brect = rawfont.boundingRect(glyph)
        brect.translate(0, ascent)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawImage(brect.topLeft(), image)
        return True


IconLayerStack = list[IconLayer]  # A stack of IconLayer objects
IconLayerOrStack = IconLayer | IconLayerStack


def ensure_icon_layer_stack(layers: IconLayerOrStack) -> IconLayerStack:
    return [layers] if isinstance(layers, IconLayer) else layers


class IconStateSpec(TupleHashMixin):
    def __init__(self, normal: IconLayerOrStack,
                 active: IconLayerOrStack = None,
                 selected: IconLayerOrStack = None,
                 disabled: IconLayerOrStack = None,
                 ):
        normal = ensure_icon_layer_stack(normal)
        active = ensure_icon_layer_stack(active or normal)
        selected = ensure_icon_layer_stack(selected or active)

        if not disabled:
            disabled = [IconLayer(x.font,
                                  *x.as_tuple()[1:-1],
                                  is_disabled_icon=True)
                        for x in normal]

        self.normal = normal
        self.active = active
        self.selected = selected
        self.disabled = ensure_icon_layer_stack(disabled)

    def get_layers_for_mode(self, mode: QIcon.Mode):
        if mode == QIcon.Mode.Active:
            return self.active
        elif mode == QIcon.Mode.Selected:
            return self.selected
        elif mode == QIcon.Mode.Disabled:
            return self.disabled
        else:
            return self.normal

    def as_tuple(self):
        return (
            tuple(layer.as_tuple() for layer in self.normal),
            tuple(layer.as_tuple() for layer in self.active),
            tuple(layer.as_tuple() for layer in self.selected),
            tuple(layer.as_tuple() for layer in self.disabled),
        )


class IconSpec(TupleHashMixin):
    _cache: IconCache = WeakValueDictionary()

    def __init__(self, on: IconStateSpec, off: IconStateSpec = None):
        self.on = on
        self.off = off or on

    def get_layers_for_state_mode(self, state: QIcon.State, mode: QIcon.Mode):
        if state == QIcon.State.Off:
            return self.off.get_layers_for_mode(mode)
        else:
            return self.on.get_layers_for_mode(mode)

    def as_tuple(self):
        return (
            self.on.as_tuple(),
            self.off.as_tuple(),
        )

    @log_func_call(DEBUGLOW2, trace_only=True)
    def icon(self):
        cache = self._cache
        cache_key = self.as_tuple()
        icon = cache.get(cache_key)
        if not icon:
            icon = QIcon(FontIconEngine(self))
            cache[cache_key] = icon

        return icon

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def generate_iconspec(cls, font: 'IconFont | type[IconFont] | str',
                          glyph_name: str = None, glyph: str | int = None):
        """
        Generate a simple IconSpec object with default settings for the given
        font and glyph.  Note that one of either `glyph_name` or `glyph` must
        be provided or a ValueError will be raised.

        Note that if `pyrandyos.gui.icons.iconfont.init_iconfonts()` has not
        been called prior to this call, "name" string values cannot be
        resolved.  Only the IconFont subclass for the font or an instance
        thereof, and the explicit "char" string or integer codepoint, may be
        passed to this method on early imports.
        Otherwise, a IconFontNotInitializedError will be raised.

        Args:
            font (IconFont | type[IconFont] | str):
                The font from which the glyph will be retrieved.  This may be
                the fontspec label as a string, an instance of its `IconFont`
                subclass, or even just the font's `IconFont` subclass itself.
            glyph_name (str, optional): The detailed name string of the
                character as listed in the character map for the font.
                Defaults to None.
            glyph (str | int, optional): Either the numeric codepoint or the
                actual Unicode character to use from the font.
                Defaults to None.

        Returns:
            IconSpec: icon spec for the given

        Raises:
            IconFontNotInitializedError: the given font has not yet been loaded
            ValueError: incorrect glyph arguments provided
        """
        return cls(IconStateSpec(IconLayer(font, glyph,
                                           glyph_name=glyph_name)))


class FontIconEngine(QIconEngine):
    def __init__(self, iconspec: IconSpec):
        super().__init__()
        self.iconspec = iconspec

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode,
              state: QIcon.State):
        iconspec = self.iconspec
        for layer in iconspec.get_layers_for_state_mode(state, mode):
            layer.paint(painter, rect)

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State):
        pm = QPixmap(size)
        pm.fill(Qt.transparent)
        self.paint(QPainter(pm), QRect(QPoint(0, 0), size), mode, state)
        return pm

    def iconName(self):
        return str(self.iconspec.as_tuple())
