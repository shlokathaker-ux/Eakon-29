import io
import json
import zipfile
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import streamlit as st
import streamlit.components.v1 as components
import yt_dlp

# ---------------------------------------------------------
# PAGE CONFIG & DARK MOCHA / ANTIQUE GOLD PALETTE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Eakon 29 — Film Emulator and Photobooth",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Space+Mono:wght@400;700&display=swap');

    /* Hide default Streamlit left sidebar, empty top header bar, and "Press Enter to submit form" overlap */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    [data-testid="stHeader"],
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Eliminate empty whitespace at the top of the page */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 2rem !important;
    }

    /* PALETTE:
       Background:     Espresso Black #1B120F
       Panels:         Dark Mocha     #2A1C16
       Borders:        Cocoa Brown    #3D2B22
       Main text:      Cream Paper    #F5E8D2
       Secondary text: Vanilla Gold   #E8D3A5
       Tiny accents:   Antique Gold   #B89454
    */
    .stApp {
        background-color: #1B120F;
        color: #F5E8D2;
        font-family: 'Space Mono', monospace;
    }

    h1, h2, h3, h4, label, p {
        color: #F5E8D2;
    }

    hr {
        border-color: #3D2B22 !important;
    }

    /* Ensure custom HTML components flow naturally in document layout without overlapping siblings */
    [data-testid="stCustomComponentV1"],
    .element-container:has(iframe) {
        height: auto !important;
        min-height: unset !important;
    }

    /* Keep top-level right column sticky so music & camera controls stay pinned while scrolling */
    [data-testid="stHorizontalBlock"]:has(.sticky-right-marker) {
        align-items: flex-start !important;
    }
    [data-testid="stHorizontalBlock"]:has(.sticky-right-marker) > [data-testid="stColumn"]:last-child {
        position: sticky !important;
        top: 1.25rem !important;
        max-height: calc(100vh - 2rem) !important;
        overflow-y: auto !important;
        padding-right: 4px !important;
        z-index: 20 !important;
    }

    /* Subtle dark mocha scrollbar if both right panels are expanded on a shorter screen */
    [data-testid="stHorizontalBlock"]:has(.sticky-right-marker) > [data-testid="stColumn"]:last-child::-webkit-scrollbar {
        width: 5px;
    }
    [data-testid="stHorizontalBlock"]:has(.sticky-right-marker) > [data-testid="stColumn"]:last-child::-webkit-scrollbar-thumb {
        background: #3D2B22;
        border-radius: 999px;
    }

    /* Centered Editorial Highlighted Brand Header */
    .brand-header {
        text-align: center;
        padding: 4px 0 20px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid #3D2B22;
    }
    .brand-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-weight: 900;
        font-style: normal !important;
        font-size: 3.9rem;
        letter-spacing: 1.5px;
        margin: 0 auto;
        line-height: 1.05;
        background: linear-gradient(120deg, #F5E8D2 0%, #E8D3A5 50%, #B89454 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 4px 22px rgba(184, 148, 84, 0.35));
    }
    .brand-subtitle {
        font-family: 'Space Mono', monospace;
        font-size: 0.95rem;
        letter-spacing: 1.6px;
        color: #E8D3A5;
        margin-top: 8px;
        display: block;
    }

    /* Empty Preview Card */
    .film-card {
        background-color: #2A1C16;
        border: 1px solid #3D2B22;
        border-radius: 12px;
        padding: 28px 20px;
        color: #E8D3A5;
    }

    /* Right-hand Control Panels & Selectboxes */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #2A1C16 !important;
        border-color: #3D2B22 !important;
        border-radius: 12px !important;
    }
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        background-color: #1B120F !important;
        border-color: #3D2B22 !important;
        color: #F5E8D2 !important;
    }

    /* Tabs styling */
    [data-baseweb="tab-list"] {
        border-bottom-color: #3D2B22 !important;
    }
    [data-baseweb="tab"] {
        color: #E8D3A5 !important;
    }
    [aria-selected="true"] {
        color: #F5E8D2 !important;
        border-bottom-color: #B89454 !important;
    }

    /* Make webcam input expand to fill its container */
    [data-testid="stCameraInput"] {
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    [data-testid="stCameraInput"] > div {
        width: 100% !important;
    }
    [data-testid="stCameraInput"] video,
    [data-testid="stCameraInput"] img {
        width: 100% !important;
        max-height: 620px;
        object-fit: cover;
        border-radius: 12px;
        border: 2px solid #3D2B22;
    }

    /* Position "Take Photo" Button on the RIGHT side of the cam window in Antique & Vanilla Gold */
    [data-testid="stCameraInput"] button {
        align-self: flex-end !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        display: block !important;
        background: linear-gradient(180deg, #E8D3A5 0%, #B89454 100%) !important;
        color: #1B120F !important;
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.4px !important;
        text-transform: none !important;
        padding: 0.45rem 1.35rem !important;
        min-height: unset !important;
        height: auto !important;
        width: auto !important;
        border-radius: 999px !important;
        border: 1px solid #F5E8D2 !important;
        box-shadow: 0 4px 14px rgba(184, 148, 84, 0.32) !important;
        transition: all 0.15s ease !important;
        margin-top: 10px !important;
    }
    [data-testid="stCameraInput"] button:hover {
        background: linear-gradient(180deg, #F5E8D2 0%, #C9A666 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(232, 211, 165, 0.45) !important;
    }
    [data-testid="stCameraInput"] button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5) !important;
    }

    /* Standard Dark Mocha & Cocoa Buttons */
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
        background-color: #2A1C16;
        color: #F5E8D2;
        border: 1px solid #B89454;
        border-radius: 8px;
        font-family: 'Space Mono', monospace;
        transition: all 0.2s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #3D2B22;
        border-color: #E8D3A5;
        color: #F5E8D2;
    }

    /* Captions in Vanilla Gold */
    [data-testid="stCaptionContainer"], small {
        color: #E8D3A5 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "film_roll" not in st.session_state:
    st.session_state.film_roll = []
if "booth_frames" not in st.session_state:
    st.session_state.booth_frames = []
if "last_layout" not in st.session_state:
    st.session_state.last_layout = "Single Frame"
if "last_capture_sig" not in st.session_state:
    st.session_state.last_capture_sig = None
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0
if "music_open" not in st.session_state:
    st.session_state.music_open = True
if "cam_menu_open" not in st.session_state:
    st.session_state.cam_menu_open = True
if "lr_queue" not in st.session_state:
    st.session_state.lr_queue = []
if "lr_play_index" not in st.session_state:
    st.session_state.lr_play_index = 0

defaults = {
    "film_stock": "Kodak Gold 200 (Warm Nostalgia)",
    "picture_layout": "Single Frame",
    "grain_amt": 0.16,
    "vignette_amt": 0.30,
    "leak_side": "None",
    "leak_amt": 0.45,
    "show_date": True,
    "custom_date": "'98 11 22",
    "mirror_selfie": False,
    "strip_theme": "Cream Paper",
    "strip_caption": "EAKON 29 // ANALOG",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.grain_amt > 0.40:
    st.session_state.grain_amt = 0.40


# ---------------------------------------------------------
# LIVE CAMERA SHUTTER CSS FILTER & GRAIN INJECTOR
# ---------------------------------------------------------
def inject_live_camera_filter(
    stock: str,
    grain: float,
    vignette: float,
    leak_side: str,
    leak_amt: float,
    date_stamp: str,
    mirror: bool,
):
    """Applies live film stock colors, animated film grain, mirror mode, vignette, light leak, and date stamp."""
    stock_filters = {
        "Kodak Gold 200 (Warm Nostalgia)": "contrast(1.08) saturate(1.18) sepia(0.24) brightness(1.03)",
        "Fujifilm Superia 400 (Crisp Greens)": "contrast(1.14) saturate(1.15) hue-rotate(-6deg) brightness(1.02)",
        "Cinestill 800T (Tungsten Night)": "contrast(1.16) saturate(1.10) hue-rotate(12deg) brightness(0.98)",
        "Ilford HP5 400 (Classic B&W)": "grayscale(1) contrast(1.32) brightness(1.02)",
        "Faded '70s Instant": "contrast(0.88) saturate(0.85) sepia(0.32) brightness(1.07)",
    }
    css_filter = stock_filters.get(stock, "none")
    css_transform = "scaleX(-1)" if mirror else "none"

    overlay_layers = []
    bg_sizes = []
    bg_repeats = []

    clamped_grain = min(max(float(grain), 0.0), 0.40)
    if clamped_grain > 0:
        alpha_coeff = round(clamped_grain * 0.62, 3)
        grain_svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
            "<filter id='g'>"
            "<feTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='3' stitchTiles='stitch'/>"
            f"<feColorMatrix type='matrix' values='1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  {alpha_coeff} {alpha_coeff} {alpha_coeff} 0 0'/>"
            "</filter>"
            "<rect width='100%' height='100%' filter='url(#g)'/>"
            "</svg>"
        )
        encoded_svg = grain_svg.replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace("'", "%22")
        overlay_layers.append(f'url("data:image/svg+xml,{encoded_svg}")')
        bg_sizes.append("180px 180px")
        bg_repeats.append("repeat")

    if leak_side != "None" and leak_amt > 0:
        if leak_side == "Left Edge Flare":
            overlay_layers.append(
                f"linear-gradient(90deg, rgba(255,110,35,{leak_amt * 0.72:.2f}) 0%, rgba(255,65,25,{leak_amt * 0.28:.2f}) 24%, transparent 45%)"
            )
        elif leak_side == "Right Corner Burn":
            overlay_layers.append(
                f"radial-gradient(circle at 95% 85%, rgba(255,120,40,{leak_amt * 0.82:.2f}) 0%, rgba(255,60,20,{leak_amt * 0.32:.2f}) 26%, transparent 50%)"
            )
        else:
            overlay_layers.append(
                f"linear-gradient(135deg, rgba(255,130,50,{leak_amt * 0.72:.2f}) 0%, rgba(255,70,30,{leak_amt * 0.25:.2f}) 28%, transparent 50%)"
            )
        bg_sizes.append("100% 100%")
        bg_repeats.append("no-repeat")

    if vignette > 0:
        edge_alpha = min(0.88, vignette * 0.98)
        overlay_layers.append(
            f"radial-gradient(circle, transparent 48%, rgba(10,6,4,{edge_alpha:.2f}) 100%)"
        )
        bg_sizes.append("100% 100%")
        bg_repeats.append("no-repeat")

    bg_overlay = ", ".join(overlay_layers) if overlay_layers else "none"
    bg_size_css = ", ".join(bg_sizes) if bg_sizes else "auto"
    bg_repeat_css = ", ".join(bg_repeats) if bg_repeats else "no-repeat"
    anim_css = "eakonLiveGrain 0.32s steps(1) infinite" if clamped_grain > 0 else "none"

    escaped_date = date_stamp.replace("\\", "\\\\").replace('"', '\\"').strip()
    date_css = ""
    if escaped_date:
        date_css = f"""
        [data-testid="stCameraInput"] div:has(> video)::before {{
            content: "{escaped_date}";
            position: absolute;
            right: 20px;
            bottom: 18px;
            font-family: 'Space Mono', monospace;
            font-weight: 700;
            font-size: 1.05rem;
            color: rgba(255, 165, 35, 0.95);
            text-shadow: 0 0 8px rgba(255, 75, 0, 0.85);
            pointer-events: none;
            z-index: 6;
        }}
        """

    st.markdown(
        f"""
        <style>
        @keyframes eakonLiveGrain {{
            0%   {{ background-position: 0px 0px, 0 0, 0 0; }}
            25%  {{ background-position: -45px 30px, 0 0, 0 0; }}
            50%  {{ background-position: 60px -50px, 0 0, 0 0; }}
            75%  {{ background-position: -25px -70px, 0 0, 0 0; }}
            100% {{ background-position: 35px 45px, 0 0, 0 0; }}
        }}
        [data-testid="stCameraInput"] video {{
            filter: {css_filter} !important;
            transform: {css_transform} !important;
            transition: filter 0.2s ease, transform 0.2s ease !important;
        }}
        [data-testid="stCameraInput"] div:has(> video) {{
            position: relative !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }}
        [data-testid="stCameraInput"] div:has(> video)::after {{
            content: "";
            position: absolute;
            inset: 0;
            background-image: {bg_overlay};
            background-size: {bg_size_css};
            background-repeat: {bg_repeat_css};
            animation: {anim_css};
            pointer-events: none;
            border-radius: 12px;
            z-index: 5;
        }}
        {date_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# LIVE SUPER 8 CAMCORDER (REAL-TIME 24FPS CANVAS + RECORDER)
# ---------------------------------------------------------
def render_super8_camcorder(
    stock: str,
    grain: float,
    vignette: float,
    leak_side: str,
    leak_amt: float,
    date_stamp: str,
    mirror: bool,
):
    """Renders a live 24fps Super 8 film camcorder and resizes both iframe and Streamlit wrapper cleanly."""
    cfg_json = json.dumps(
        {
            "stock": stock,
            "grain": float(grain),
            "vignette": float(vignette),
            "leakSide": leak_side,
            "leakAmt": float(leak_amt),
            "dateStamp": date_stamp,
            "mirror": bool(mirror),
        }
    )

    super8_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

      * {{ box-sizing: border-box; margin: 0; padding: 0; }}

      html, body {{
        background: transparent;
        color: #F5E8D2;
        font-family: 'Space Mono', monospace;
        overflow: hidden;
      }}

      .s8-shell {{
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding-bottom: 10px;
      }}

      .viewfinder-box {{
        position: relative;
        width: 100%;
        height: 460px;
        background: #2A1C16;
        border: 2px solid #3D2B22;
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
      }}

      canvas#s8Canvas {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: none;
      }}

      .hud-overlay {{
        position: absolute;
        inset: 0;
        pointer-events: none;
        display: none;
        flex-direction: column;
        justify-content: space-between;
        padding: 14px 18px;
      }}

      .hud-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
      }}

      .rec-badge {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(27, 18, 15, 0.78);
        border: 1px solid #3D2B22;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        color: #F5E8D2;
      }}

      .rec-dot {{
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #8c6d53;
      }}

      .rec-badge.recording .rec-dot {{
        background: #e63946;
        box-shadow: 0 0 10px #e63946;
        animation: blinkRec 1s infinite;
      }}

      @keyframes blinkRec {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0.25; }}
      }}

      .stock-tag {{
        background: rgba(27, 18, 15, 0.78);
        border: 1px solid #3D2B22;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        color: #E8D3A5;
      }}

      .reticle-tl, .reticle-tr, .reticle-bl, .reticle-br {{
        position: absolute;
        width: 18px;
        height: 18px;
        border-color: rgba(245, 232, 210, 0.55);
        border-style: solid;
      }}
      .reticle-tl {{ top: 48px; left: 22px; border-width: 2px 0 0 2px; }}
      .reticle-tr {{ top: 48px; right: 22px; border-width: 2px 2px 0 0; }}
      .reticle-bl {{ bottom: 48px; left: 22px; border-width: 0 0 2px 2px; }}
      .reticle-br {{ bottom: 48px; right: 22px; border-width: 0 2px 2px 0; }}

      .idle-prompt {{
        text-align: center;
        padding: 24px;
        color: #E8D3A5;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
      }}

      .idle-prompt p {{
        font-size: 0.86rem;
        max-width: 360px;
        line-height: 1.5;
      }}

      .controls-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }}

      .btn-s8 {{
        background: #2A1C16;
        color: #F5E8D2;
        border: 1px solid #B89454;
        border-radius: 999px;
        padding: 0.48rem 1.25rem;
        font-family: 'Space Mono', monospace;
        font-size: 0.85rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.15s ease;
      }}

      .btn-s8:hover:not(:disabled) {{
        background: #3D2B22;
        border-color: #E8D3A5;
      }}

      .btn-s8:disabled {{
        opacity: 0.45;
        cursor: not-allowed;
      }}

      .btn-gold {{
        background: linear-gradient(180deg, #E8D3A5 0%, #B89454 100%);
        color: #1B120F;
        border: 1px solid #F5E8D2;
        box-shadow: 0 4px 14px rgba(184, 148, 84, 0.32);
      }}

      .btn-gold:hover:not(:disabled) {{
        background: linear-gradient(180deg, #F5E8D2 0%, #C9A666 100%);
        color: #1B120F;
        transform: translateY(-1px);
      }}

      .btn-rec-active {{
        background: linear-gradient(180deg, #d94e4e 0%, #9e2a2b 100%);
        color: #F5E8D2;
        border: 1px solid #F5E8D2;
      }}

      .playback-card {{
        display: none;
        flex-direction: column;
        gap: 10px;
        background: #2A1C16;
        border: 1px solid #3D2B22;
        border-radius: 12px;
        padding: 14px;
        margin-top: 4px;
      }}

      .playback-card.visible {{
        display: flex;
      }}

      .playback-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
        color: #E8D3A5;
      }}

      video#recordedPlayback {{
        width: 100%;
        height: 420px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #3D2B22;
        background: #1B120F;
      }}

      a.dl-link {{
        text-decoration: none;
        text-align: center;
        display: block;
      }}
    </style>
    </head>
    <body>
      <div class="s8-shell" id="s8Shell">
        <div class="viewfinder-box">
          <div class="idle-prompt" id="idlePrompt">
            <p>Load the Super 8 film cartridge to preview live 24fps analog color, grain, and light leaks.</p>
            <button type="button" class="btn-s8 btn-gold" id="startCamBtn">Open Super 8 Viewfinder</button>
          </div>

          <canvas id="s8Canvas" width="800" height="600"></canvas>

          <div class="hud-overlay" id="hudOverlay">
            <div class="hud-top">
              <div class="rec-badge" id="recBadge">
                <span class="rec-dot"></span>
                <span id="recTimer">STBY • 00:00</span>
              </div>
              <div class="stock-tag" id="hudStockLabel">24 FPS • SUPER 8</div>
            </div>
            <div class="reticle-tl"></div>
            <div class="reticle-tr"></div>
            <div class="reticle-bl"></div>
            <div class="reticle-br"></div>
          </div>
        </div>

        <div class="controls-bar">
          <button type="button" class="btn-s8" id="stopCamBtn" style="display:none;">Close Lens</button>
          <div style="margin-left:auto; display:flex; gap:8px;">
            <button type="button" class="btn-s8 btn-gold" id="recBtn" disabled>● Record Super 8</button>
          </div>
        </div>

        <div class="playback-card" id="playbackCard">
          <div class="playback-header">
            <span>🎞️ Developed Super 8 Reel</span>
            <span id="clipMeta">Ready</span>
          </div>
          <video id="recordedPlayback" controls playsinline loop></video>
          <a id="downloadClipBtn" class="btn-s8 btn-gold dl-link" download="eakon29_super8.webm">
            ⬇️ Download Super 8 Clip
          </a>
        </div>
      </div>

      <video id="rawWebcam" autoplay playsinline muted style="display:none;"></video>

      <script>
      (function() {{
        const cfg = {cfg_json};
        const pWin = window.parent;

        // Resize BOTH the iframe AND Streamlit's outer wrapper containers so content below shifts down cleanly
        function syncIframeHeight() {{
          try {{
            const shell = document.getElementById("s8Shell");
            if (!shell || !window.frameElement) return;
            const targetH = Math.ceil(shell.getBoundingClientRect().height) + 12;
            const iframe = window.frameElement;
            iframe.style.height = targetH + "px";
            iframe.setAttribute("height", String(targetH));

            let parent = iframe.parentElement;
            for (let i = 0; i < 3 && parent; i++) {{
              if (parent.style && parent.style.height) {{
                parent.style.height = targetH + "px";
              }}
              parent = parent.parentElement;
            }}
          }} catch (e) {{}}
        }}

        const ro = new ResizeObserver(() => requestAnimationFrame(syncIframeHeight));
        ro.observe(document.getElementById("s8Shell"));
        syncIframeHeight();
        setTimeout(syncIframeHeight, 150);

        pWin.__eakonSuper8Cfg = cfg;

        const startCamBtn = document.getElementById("startCamBtn");
        const stopCamBtn = document.getElementById("stopCamBtn");
        const recBtn = document.getElementById("recBtn");
        const idlePrompt = document.getElementById("idlePrompt");
        const hudOverlay = document.getElementById("hudOverlay");
        const hudStockLabel = document.getElementById("hudStockLabel");
        const recBadge = document.getElementById("recBadge");
        const recTimer = document.getElementById("recTimer");
        const canvas = document.getElementById("s8Canvas");
        const ctx = canvas.getContext("2d", {{ willReadFrequently: true }});
        const rawVideo = document.getElementById("rawWebcam");
        const playbackCard = document.getElementById("playbackCard");
        const recordedPlayback = document.getElementById("recordedPlayback");
        const downloadClipBtn = document.getElementById("downloadClipBtn");

        hudStockLabel.textContent = "24 FPS • " + cfg.stock.split(" (")[0].toUpperCase();

        const grainCanvas = document.createElement("canvas");
        grainCanvas.width = 256;
        grainCanvas.height = 256;
        const gCtx = grainCanvas.getContext("2d");

        function regenerateGrainTile() {{
          const imgData = gCtx.createImageData(256, 256);
          const d = imgData.data;
          for (let i = 0; i < d.length; i += 4) {{
            const v = 128 + (Math.random() - 0.5) * 150;
            d[i] = v;
            d[i + 1] = v;
            d[i + 2] = v;
            d[i + 3] = 255;
          }}
          gCtx.putImageData(imgData, 0, 0);
        }}
        regenerateGrainTile();

        let stream = null;
        let renderInterval = null;
        let mediaRecorder = null;
        let recordedChunks = [];
        let isRecording = false;
        let recStartTime = 0;
        let timerInterval = null;

        function getStockCssFilter(stockName) {{
          if (stockName === "Kodak Gold 200 (Warm Nostalgia)") {{
            return "contrast(1.08) saturate(1.18) sepia(0.24) brightness(1.03)";
          }} else if (stockName === "Fujifilm Superia 400 (Crisp Greens)") {{
            return "contrast(1.14) saturate(1.15) hue-rotate(-6deg) brightness(1.02)";
          }} else if (stockName === "Cinestill 800T (Tungsten Night)") {{
            return "contrast(1.16) saturate(1.10) hue-rotate(12deg) brightness(0.98)";
          }} else if (stockName === "Ilford HP5 400 (Classic B&W)") {{
            return "grayscale(1) contrast(1.32) brightness(1.02)";
          }} else if (stockName === "Faded '70s Instant") {{
            return "contrast(0.88) saturate(0.85) sepia(0.32) brightness(1.07)";
          }}
          return "none";
        }}

        function drawFrame() {{
          if (!stream || rawVideo.readyState < 2) return;
          const activeCfg = pWin.__eakonSuper8Cfg || cfg;
          const w = canvas.width;
          const h = canvas.height;

          ctx.save();
          ctx.fillStyle = "#1B120F";
          ctx.fillRect(0, 0, w, h);

          const jitterX = (Math.random() - 0.5) * 2.2;
          const jitterY = (Math.random() - 0.5) * 2.6;

          ctx.filter = getStockCssFilter(activeCfg.stock);
          if (activeCfg.mirror) {{
            ctx.translate(w + jitterX, jitterY);
            ctx.scale(-1, 1);
            ctx.drawImage(rawVideo, 0, 0, w, h);
          }} else {{
            ctx.drawImage(rawVideo, jitterX, jitterY, w, h);
          }}
          ctx.restore();

          if (activeCfg.stock === "Cinestill 800T (Tungsten Night)") {{
            ctx.fillStyle = "rgba(25, 65, 115, 0.14)";
            ctx.fillRect(0, 0, w, h);
          }} else if (activeCfg.stock === "Kodak Gold 200 (Warm Nostalgia)") {{
            ctx.fillStyle = "rgba(255, 175, 75, 0.08)";
            ctx.fillRect(0, 0, w, h);
          }}

          if (activeCfg.leakSide !== "None" && activeCfg.leakAmt > 0) {{
            ctx.save();
            ctx.globalCompositeOperation = "screen";
            let grad;
            if (activeCfg.leakSide === "Left Edge Flare") {{
              grad = ctx.createLinearGradient(0, 0, w * 0.42, 0);
              grad.addColorStop(0, `rgba(255, 110, 35, ${{activeCfg.leakAmt * 0.85}})`);
              grad.addColorStop(0.5, `rgba(255, 65, 25, ${{activeCfg.leakAmt * 0.35}})`);
              grad.addColorStop(1, "rgba(255, 65, 25, 0)");
            }} else if (activeCfg.leakSide === "Right Corner Burn") {{
              grad = ctx.createRadialGradient(w * 0.96, h * 0.85, 10, w * 0.92, h * 0.82, w * 0.45);
              grad.addColorStop(0, `rgba(255, 120, 40, ${{activeCfg.leakAmt * 0.9}})`);
              grad.addColorStop(1, "rgba(255, 60, 20, 0)");
            }} else {{
              grad = ctx.createLinearGradient(0, 0, w * 0.5, h * 0.5);
              grad.addColorStop(0, `rgba(255, 130, 50, ${{activeCfg.leakAmt * 0.8}})`);
              grad.addColorStop(1, "rgba(255, 70, 30, 0)");
            }}
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, w, h);
            ctx.restore();
          }}

          if (activeCfg.vignette > 0) {{
            const vig = ctx.createRadialGradient(w / 2, h / 2, w * 0.28, w / 2, h / 2, w * 0.72);
            vig.addColorStop(0, "rgba(0,0,0,0)");
            vig.addColorStop(1, `rgba(10, 6, 4, ${{Math.min(0.92, activeCfg.vignette * 1.05)}})`);
            ctx.fillStyle = vig;
            ctx.fillRect(0, 0, w, h);
          }}

          if (activeCfg.grain > 0) {{
            ctx.save();
            ctx.globalCompositeOperation = "overlay";
            ctx.globalAlpha = Math.min(0.45, activeCfg.grain * 1.15);
            const ox = Math.floor(Math.random() * 128);
            const oy = Math.floor(Math.random() * 128);
            ctx.drawImage(grainCanvas, -ox, -oy, w + 128, h + 128);
            ctx.restore();
          }}

          if (activeCfg.dateStamp && activeCfg.dateStamp.trim() !== "") {{
            ctx.save();
            ctx.font = "bold 24px 'Space Mono', monospace";
            ctx.textAlign = "right";
            ctx.shadowColor = "rgba(255, 75, 0, 0.85)";
            ctx.shadowBlur = 8;
            ctx.fillStyle = "rgba(255, 165, 35, 0.94)";
            ctx.fillText(activeCfg.dateStamp, w - 28, h - 24);
            ctx.restore();
          }}
        }}

        async function startCamera() {{
          try {{
            stream = await navigator.mediaDevices.getUserMedia({{
              video: {{ width: {{ ideal: 800 }}, height: {{ ideal: 600 }}, facingMode: "user" }},
              audio: true
            }});
          }} catch (err) {{
            stream = await navigator.mediaDevices.getUserMedia({{
              video: {{ width: {{ ideal: 800 }}, height: {{ ideal: 600 }}, facingMode: "user" }},
              audio: false
            }});
          }}

          rawVideo.srcObject = stream;
          await rawVideo.play();

          idlePrompt.style.display = "none";
          canvas.style.display = "block";
          hudOverlay.style.display = "flex";
          stopCamBtn.style.display = "inline-block";
          recBtn.disabled = false;
          syncIframeHeight();

          renderInterval = setInterval(drawFrame, 1000 / 24);
        }}

        function stopCamera() {{
          if (isRecording) stopRecording();
          if (renderInterval) clearInterval(renderInterval);
          if (stream) {{
            stream.getTracks().forEach(t => t.stop());
            stream = null;
          }}
          canvas.style.display = "none";
          hudOverlay.style.display = "none";
          stopCamBtn.style.display = "none";
          idlePrompt.style.display = "flex";
          recBtn.disabled = true;
          syncIframeHeight();
        }}

        function formatElapsed(ms) {{
          const totalSec = Math.floor(ms / 1000);
          const m = Math.floor(totalSec / 60);
          const s = totalSec % 60;
          return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
        }}

        function startRecording() {{
          recordedChunks = [];
          const canvasStream = canvas.captureStream(24);

          const audioTracks = stream ? stream.getAudioTracks() : [];
          if (audioTracks.length > 0) {{
            canvasStream.addTrack(audioTracks[0]);
          }}

          let mimeType = "video/webm;codecs=vp9";
          let ext = "webm";
          if (MediaRecorder.isTypeSupported("video/mp4")) {{
            mimeType = "video/mp4";
            ext = "mp4";
          }} else if (!MediaRecorder.isTypeSupported(mimeType)) {{
            mimeType = "video/webm";
          }}

          mediaRecorder = new MediaRecorder(canvasStream, {{ mimeType }});
          mediaRecorder.ondataavailable = e => {{
            if (e.data && e.data.size > 0) recordedChunks.push(e.data);
          }};

          mediaRecorder.onstop = () => {{
            const blob = new Blob(recordedChunks, {{ type: mimeType }});
            const url = URL.createObjectURL(blob);
            recordedPlayback.src = url;
            downloadClipBtn.href = url;
            const stamp = new Date().toTimeString().slice(0, 8).replace(/:/g, "");
            downloadClipBtn.download = `eakon29_super8_${{stamp}}.${{ext}}`;
            document.getElementById("clipMeta").textContent = `${{(blob.size / (1024 * 1024)).toFixed(1)}} MB • .${{ext.toUpperCase()}}`;
            playbackCard.classList.add("visible");
            syncIframeHeight();
            setTimeout(syncIframeHeight, 100);
          }};

          mediaRecorder.start(200);
          isRecording = true;
          recStartTime = Date.now();
          recBadge.classList.add("recording");
          recBtn.classList.remove("btn-gold");
          recBtn.classList.add("btn-rec-active");
          recBtn.textContent = "■ Stop Recording";

          timerInterval = setInterval(() => {{
            recTimer.textContent = "REC • " + formatElapsed(Date.now() - recStartTime);
          }}, 250);
        }}

        function stopRecording() {{
          if (mediaRecorder && mediaRecorder.state !== "inactive") {{
            mediaRecorder.stop();
          }}
          isRecording = false;
          if (timerInterval) clearInterval(timerInterval);
          recBadge.classList.remove("recording");
          recTimer.textContent = "STBY • 00:00";
          recBtn.classList.remove("btn-rec-active");
          recBtn.classList.add("btn-gold");
          recBtn.textContent = "● Record Super 8";
        }}

        startCamBtn.onclick = startCamera;
        stopCamBtn.onclick = stopCamera;
        recBtn.onclick = () => {{
          if (!isRecording) startRecording();
          else stopRecording();
        }};
      }})();
      </script>
    </body>
    </html>
    """
    components.html(super8_html, height=535)


# ---------------------------------------------------------
# LISTEN TO MUSIC (YOUTUBE SEARCH + THEME-MATCHED VINYL DECK)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def search_youtube_song(query: str) -> dict | None:
    """Searches YouTube by song name without an API key and returns metadata + video ID."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "default_search": "ytsearch1",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries") or []
            if not entries:
                return None
            top = entries[0]
            vid_id = top.get("id")
            if not vid_id:
                return None
            return {
                "videoId": vid_id,
                "title": top.get("title") or query,
                "artist": top.get("uploader") or top.get("channel") or "YouTube Audio",
            }
    except Exception:
        return None


def render_music_box():
    """Renders the standalone, collapsible 'Listen to Music' box with a theme-locked spinning vinyl."""
    with st.container(border=True):
        m_head, m_min = st.columns([4, 1])
        with m_head:
            st.subheader("🎵 Listen to Music")
        with m_min:
            if st.button("▶", key="min_music_btn", help="Minimize Listen to Music", use_container_width=True):
                st.session_state.music_open = False
                st.rerun()

        with st.form("yt_song_search_form", clear_on_submit=True):
            s_col, b_col = st.columns([3.2, 1], gap="small")
            with s_col:
                song_query = st.text_input(
                    "Search song",
                    placeholder="Search any song name...",
                    label_visibility="collapsed",
                )
            with b_col:
                submitted = st.form_submit_button("Play", use_container_width=True)

        if submitted and song_query.strip():
            with st.spinner("Tuning frequency..."):
                track = search_youtube_song(song_query.strip())
            if track:
                st.session_state.lr_queue.append(track)
                st.session_state.lr_play_index = len(st.session_state.lr_queue) - 1
            else:
                st.toast("Couldn't find that song—try adding the artist name!", icon="📻")

        queue_json = json.dumps(st.session_state.lr_queue)
        target_idx = st.session_state.lr_play_index

        player_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8" />
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

          * {{ box-sizing: border-box; margin: 0; padding: 0; }}

          body {{
            background: transparent;
            color: #F5E8D2;
            font-family: 'Space Mono', monospace;
            overflow: hidden;
          }}

          .listening-room {{
            background: #1B120F;
            border: 1px solid #3D2B22;
            border-radius: 10px;
            padding: 12px 13px;
            display: flex;
            flex-direction: column;
            gap: 9px;
          }}

          .lr-main {{
            display: flex;
            align-items: center;
            gap: 11px;
          }}

          .disc-wrap {{
            position: relative;
            width: 52px;
            height: 52px;
            min-width: 52px;
            border-radius: 50%;
            border: 1.5px solid #B89454;
            background: #1B120F;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 3px 12px rgba(0, 0, 0, 0.55);
            overflow: hidden;
          }}

          .disc-spin {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: spinDisc 5.5s linear infinite;
            animation-play-state: paused;
          }}

          .disc-spin.playing {{
            animation-play-state: running;
          }}

          @keyframes spinDisc {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
          }}

          .disc-spindle {{
            position: absolute;
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #1B120F;
            border: 1.8px solid #F5E8D2;
            z-index: 2;
          }}

          .track-meta {{
            flex: 1;
            min-width: 0;
          }}

          .track-title {{
            font-size: 0.78rem;
            font-weight: 700;
            color: #F5E8D2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }}

          .track-artist {{
            font-size: 0.68rem;
            color: #E8D3A5;
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }}

          .track-status {{
            font-size: 0.63rem;
            color: #B89454;
            margin-top: 2px;
          }}

          .progress-wrap {{
            display: flex;
            flex-direction: column;
            gap: 3px;
          }}

          input[type="range"].seek-bar {{
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 4px;
            background: #3D2B22;
            border-radius: 999px;
            outline: none;
            cursor: pointer;
          }}

          input[type="range"].seek-bar::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 11px;
            height: 11px;
            border-radius: 50%;
            background: #E8D3A5;
            border: 1.5px solid #B89454;
            cursor: pointer;
          }}

          .time-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.64rem;
            color: #E8D3A5;
          }}

          .controls-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
          }}

          .transport-group {{
            display: flex;
            align-items: center;
            gap: 5px;
          }}

          .btn-ctrl {{
            background: #2A1C16;
            color: #F5E8D2;
            border: 1px solid #3D2B22;
            border-radius: 7px;
            height: 29px;
            min-width: 29px;
            padding: 0 7px;
            font-family: 'Space Mono', monospace;
            font-size: 0.76rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.16s ease;
          }}

          .btn-ctrl:hover {{
            background: #3D2B22;
            border-color: #B89454;
          }}

          .btn-play {{
            background: linear-gradient(180deg, #E8D3A5 0%, #B89454 100%);
            color: #1B120F;
            border: 1px solid #F5E8D2;
            font-weight: 700;
            min-width: 34px;
          }}

          .btn-play:hover {{
            background: linear-gradient(180deg, #F5E8D2 0%, #C9A666 100%);
            color: #1B120F;
          }}

          .vol-group {{
            display: flex;
            align-items: center;
            gap: 4px;
            justify-content: flex-end;
          }}

          input[type="range"].vol-bar {{
            -webkit-appearance: none;
            appearance: none;
            width: 52px;
            height: 3.5px;
            background: #3D2B22;
            border-radius: 999px;
            outline: none;
            cursor: pointer;
          }}

          input[type="range"].vol-bar::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #B89454;
            cursor: pointer;
          }}
        </style>
        </head>
        <body>
          <div class="listening-room" role="region" aria-label="Listen to Music Audio Player">
            <div class="lr-main">
              <div class="disc-wrap" aria-hidden="true">
                <div class="disc-spin" id="discSpin">
                  <svg viewBox="0 0 60 60" width="52" height="52">
                    <circle cx="30" cy="30" r="28" fill="#1B120F" />
                    <path d="M 30 2 A 28 28 0 0 1 54 16 L 30 30 Z" fill="#2A1C16" opacity="0.85" />
                    <path d="M 30 58 A 28 28 0 0 1 6 44 L 30 30 Z" fill="#2A1C16" opacity="0.85" />
                    <circle cx="30" cy="30" r="24" fill="none" stroke="#3D2B22" stroke-width="0.9" />
                    <circle cx="30" cy="30" r="20" fill="none" stroke="#3D2B22" stroke-width="0.8" />
                    <circle cx="30" cy="30" r="16" fill="none" stroke="#3D2B22" stroke-width="0.9" />
                    <circle cx="30" cy="30" r="11.5" fill="#B89454" />
                    <circle cx="30" cy="30" r="9" fill="none" stroke="#F5E8D2" stroke-width="0.6" stroke-dasharray="3 2" />
                    <circle cx="30" cy="23.5" r="1.2" fill="#F5E8D2" />
                  </svg>
                </div>
                <div class="disc-spindle"></div>
              </div>

              <div class="track-meta">
                <div class="track-title" id="trackTitle">No song queued</div>
                <div class="track-artist" id="trackArtist">Search above to play any song</div>
                <div class="track-status" id="trackStatus">00 / 00 · Idle</div>
              </div>
            </div>

            <div class="progress-wrap">
              <input type="range" id="seekBar" class="seek-bar" min="0" max="100" value="0" step="0.5" aria-label="Playback position" />
              <div class="time-row">
                <span id="currTime">0:00</span>
                <span id="totTime">0:00</span>
              </div>
            </div>

            <div class="controls-row">
              <div class="transport-group">
                <button type="button" class="btn-ctrl" id="prevBtn" aria-label="Previous track">⏮</button>
                <button type="button" class="btn-ctrl btn-play" id="playBtn" aria-label="Play">▶</button>
                <button type="button" class="btn-ctrl" id="nextBtn" aria-label="Next track">⏭</button>
              </div>
              <div class="vol-group">
                <button type="button" class="btn-ctrl" id="muteBtn" aria-label="Mute or unmute">🔊</button>
                <input type="range" id="volBar" class="vol-bar" min="0" max="100" step="2" value="75" aria-label="Volume" />
              </div>
            </div>
          </div>

          <script>
          (function() {{
            const queue = {queue_json};
            const requestedIndex = {target_idx};
            const pWin = window.parent;
            const pDoc = pWin.document;

            if (!pWin.__eakonYT) {{
              pWin.__eakonYT = {{
                player: null,
                ready: false,
                queue: [],
                index: 0,
                loadedVideoId: "",
                pendingVideoId: "",
                isPlaying: false
              }};

              const hostDiv = pDoc.createElement("div");
              hostDiv.id = "eakon-yt-hidden-host";
              hostDiv.style.position = "fixed";
              hostDiv.style.width = "1px";
              hostDiv.style.height = "1px";
              hostDiv.style.opacity = "0.001";
              hostDiv.style.pointerEvents = "none";
              hostDiv.style.bottom = "0";
              hostDiv.style.right = "0";
              pDoc.body.appendChild(hostDiv);

              const inner = pDoc.createElement("div");
              inner.id = "eakon-yt-player-el";
              hostDiv.appendChild(inner);

              pWin.onYouTubeIframeAPIReady = function() {{
                pWin.__eakonYT.player = new pWin.YT.Player("eakon-yt-player-el", {{
                  height: "1",
                  width: "1",
                  playerVars: {{
                    autoplay: 0,
                    controls: 0,
                    disablekb: 1,
                    playsinline: 1
                  }},
                  events: {{
                    onReady: function(ev) {{
                      pWin.__eakonYT.ready = true;
                      ev.target.setVolume(75);
                      if (pWin.__eakonYT.pendingVideoId) {{
                        ev.target.loadVideoById(pWin.__eakonYT.pendingVideoId);
                        pWin.__eakonYT.loadedVideoId = pWin.__eakonYT.pendingVideoId;
                        pWin.__eakonYT.pendingVideoId = "";
                      }}
                    }},
                    onStateChange: function(ev) {{
                      const YTState = pWin.YT.PlayerState;
                      pWin.__eakonYT.isPlaying = (ev.data === YTState.PLAYING);
                      if (ev.data === YTState.ENDED && pWin.__eakonYT.queue.length > 0) {{
                        const nextIdx = (pWin.__eakonYT.index + 1) % pWin.__eakonYT.queue.length;
                        pWin.__eakonYT.index = nextIdx;
                        const nextTrack = pWin.__eakonYT.queue[nextIdx];
                        pWin.__eakonYT.loadedVideoId = nextTrack.videoId;
                        ev.target.loadVideoById(nextTrack.videoId);
                      }}
                    }}
                  }}
                }});
              }};

              const tag = pDoc.createElement("script");
              tag.src = "https://www.youtube.com/iframe_api";
              pDoc.head.appendChild(tag);
            }}

            const ytState = pWin.__eakonYT;
            ytState.queue = queue;

            const trackTitle = document.getElementById("trackTitle");
            const trackArtist = document.getElementById("trackArtist");
            const trackStatus = document.getElementById("trackStatus");
            const discSpin = document.getElementById("discSpin");
            const seekBar = document.getElementById("seekBar");
            const currTime = document.getElementById("currTime");
            const totTime = document.getElementById("totTime");
            const playBtn = document.getElementById("playBtn");
            const prevBtn = document.getElementById("prevBtn");
            const nextBtn = document.getElementById("nextBtn");
            const muteBtn = document.getElementById("muteBtn");
            const volBar = document.getElementById("volBar");

            function fmt(sec) {{
              if (!isFinite(sec) || sec < 0) return "0:00";
              const m = Math.floor(sec / 60);
              const s = Math.floor(sec % 60);
              return m + ":" + (s < 10 ? "0" : "") + s;
            }}

            function playIndex(idx) {{
              if (!ytState.queue.length) return;
              ytState.index = (idx + ytState.queue.length) % ytState.queue.length;
              const t = ytState.queue[ytState.index];
              ytState.loadedVideoId = t.videoId;
              if (ytState.ready && ytState.player) {{
                ytState.player.loadVideoById(t.videoId);
              }} else {{
                ytState.pendingVideoId = t.videoId;
              }}
            }}

            if (queue.length > 0) {{
              const newest = queue[requestedIndex];
              if (newest && newest.videoId !== ytState.loadedVideoId) {{
                playIndex(requestedIndex);
              }}
            }}

            function refreshUI() {{
              const total = ytState.queue.length;
              if (!total) {{
                trackTitle.textContent = "No song queued";
                trackArtist.textContent = "Search above to play any song";
                trackStatus.textContent = "00 / 00 · Ready";
                playBtn.textContent = "▶";
                discSpin.classList.remove("playing");
                return;
              }}

              const t = ytState.queue[ytState.index] || ytState.queue[0];
              const posStr = String(ytState.index + 1).padStart(2, "0") + " / " + String(total).padStart(2, "0");

              trackTitle.textContent = t.title;
              trackArtist.textContent = t.artist;

              if (ytState.isPlaying) {{
                playBtn.textContent = "❚❚";
                playBtn.setAttribute("aria-label", "Pause");
                discSpin.classList.add("playing");
                trackStatus.textContent = posStr + " · Now spinning";
              }} else {{
                playBtn.textContent = "▶";
                playBtn.setAttribute("aria-label", "Play");
                discSpin.classList.remove("playing");
                trackStatus.textContent = posStr + " · Paused";
              }}

              if (ytState.ready && ytState.player && typeof ytState.player.getDuration === "function") {{
                const dur = ytState.player.getDuration();
                const cur = ytState.player.getCurrentTime();
                if (dur > 0) {{
                  seekBar.max = dur;
                  seekBar.value = cur;
                  currTime.textContent = fmt(cur);
                  totTime.textContent = fmt(dur);
                }}
                const muted = ytState.player.isMuted();
                const vol = ytState.player.getVolume();
                volBar.value = muted ? 0 : vol;
                muteBtn.textContent = (muted || vol === 0) ? "🔇" : "🔊";
              }}
            }}

            playBtn.onclick = function() {{
              if (!ytState.ready || !ytState.player || !ytState.queue.length) return;
              if (ytState.isPlaying) {{
                ytState.player.pauseVideo();
              }} else {{
                ytState.player.playVideo();
              }}
              setTimeout(refreshUI, 120);
            }};

            prevBtn.onclick = function() {{
              if (!ytState.queue.length) return;
              if (ytState.ready && ytState.player && ytState.player.getCurrentTime() > 3) {{
                ytState.player.seekTo(0, true);
              }} else {{
                playIndex(ytState.index - 1);
              }}
              setTimeout(refreshUI, 150);
            }};

            nextBtn.onclick = function() {{
              if (!ytState.queue.length) return;
              playIndex(ytState.index + 1);
              setTimeout(refreshUI, 150);
            }};

            seekBar.oninput = function() {{
              if (ytState.ready && ytState.player) {{
                ytState.player.seekTo(parseFloat(seekBar.value), true);
                currTime.textContent = fmt(parseFloat(seekBar.value));
              }}
            }};

            volBar.oninput = function() {{
              if (!ytState.ready || !ytState.player) return;
              const v = parseInt(volBar.value, 10);
              ytState.player.setVolume(v);
              if (v === 0) ytState.player.mute();
              else ytState.player.unMute();
              refreshUI();
            }};

            muteBtn.onclick = function() {{
              if (!ytState.ready || !ytState.player) return;
              if (ytState.player.isMuted()) {{
                ytState.player.unMute();
              }} else {{
                ytState.player.mute();
              }}
              refreshUI();
            }};

            refreshUI();
            setInterval(refreshUI, 500);
          }})();
          </script>
        </body>
        </html>
        """
        components.html(player_html, height=175)


def render_camera_settings_box():
    """Renders the standalone, collapsible 'Choose Your Camera' box."""
    with st.container(border=True):
        head_col, min_col = st.columns([4, 1])
        with head_col:
            st.subheader("📷 Choose Your Camera")
        with min_col:
            if st.button("▶", key="min_cam_btn", help="Minimize Choose Your Camera", use_container_width=True):
                st.session_state.cam_menu_open = False
                st.rerun()

        st.session_state.film_stock = st.selectbox(
            "Choose Lens & Film Stock",
            [
                "Kodak Gold 200 (Warm Nostalgia)",
                "Fujifilm Superia 400 (Crisp Greens)",
                "Cinestill 800T (Tungsten Night)",
                "Ilford HP5 400 (Classic B&W)",
                "Faded '70s Instant",
            ],
            index=[
                "Kodak Gold 200 (Warm Nostalgia)",
                "Fujifilm Superia 400 (Crisp Greens)",
                "Cinestill 800T (Tungsten Night)",
                "Ilford HP5 400 (Classic B&W)",
                "Faded '70s Instant",
            ].index(st.session_state.film_stock),
        )

        st.session_state.picture_layout = st.selectbox(
            "Choose Picture Layout",
            ["Single Frame", "2-Cut", "3-Cut", "4-Cut Photostrip"],
            index=["Single Frame", "2-Cut", "3-Cut", "4-Cut Photostrip"].index(
                st.session_state.picture_layout
            ),
        )

        if st.session_state.picture_layout != st.session_state.last_layout:
            st.session_state.booth_frames = []
            st.session_state.last_layout = st.session_state.picture_layout

        st.divider()
        st.session_state.grain_amt = st.slider(
            "Film Grain (ISO)", 0.00, 0.40, float(st.session_state.grain_amt), 0.02
        )
        st.session_state.vignette_amt = st.slider(
            "Lens Vignette", 0.0, 0.85, float(st.session_state.vignette_amt), 0.05
        )
        st.session_state.leak_side = st.selectbox(
            "Light Leak",
            ["None", "Left Edge Flare", "Right Corner Burn", "Top Diagonal Streak"],
            index=["None", "Left Edge Flare", "Right Corner Burn", "Top Diagonal Streak"].index(
                st.session_state.leak_side
            ),
        )
        if st.session_state.leak_side != "None":
            st.session_state.leak_amt = st.slider(
                "Light Leak Intensity", 0.0, 1.0, float(st.session_state.leak_amt), 0.05
            )

        st.divider()
        st.session_state.show_date = st.checkbox(
            "Quartz Date Stamp ('98 Style)", value=st.session_state.show_date
        )
        if st.session_state.show_date:
            st.session_state.custom_date = st.text_input(
                "Date Stamp Text", value=st.session_state.custom_date
            )
        st.session_state.mirror_selfie = st.checkbox(
            "Mirror Image (Selfie Mode)", value=st.session_state.mirror_selfie
        )

        if st.session_state.picture_layout != "Single Frame":
            st.divider()
            st.session_state.strip_theme = st.selectbox(
                "Strip Border Color",
                ["Cream Paper", "Espresso Black", "Dark Mocha", "Vanilla Gold"],
                index=[
                    "Cream Paper",
                    "Espresso Black",
                    "Dark Mocha",
                    "Vanilla Gold",
                ].index(st.session_state.strip_theme),
            )
            st.session_state.strip_caption = st.text_input(
                "Strip Caption", value=st.session_state.strip_caption
            )


# ---------------------------------------------------------
# MECHANICAL SHUTTER CLICK SOUND + FLASH EFFECT
# ---------------------------------------------------------
def trigger_shutter_effect():
    """Plays an authentic mechanical leaf-shutter click + film advance and triggers a brief flash."""
    components.html(
        """
        <script>
        (function() {
            try {
                const parentDoc = window.parent.document;
                const flash = parentDoc.createElement('div');
                flash.style.position = 'fixed';
                flash.style.inset = '0';
                flash.style.backgroundColor = '#F5E8D2';
                flash.style.opacity = '0.88';
                flash.style.zIndex = '999999';
                flash.style.pointerEvents = 'none';
                flash.style.transition = 'opacity 0.28s ease-out';
                parentDoc.body.appendChild(flash);
                requestAnimationFrame(() => {
                    flash.style.opacity = '0';
                    setTimeout(() => flash.remove(), 320);
                });

                const AudioCtx = window.parent.AudioContext || window.parent.webkitAudioContext;
                const ctx = new AudioCtx();
                if (ctx.state === 'suspended') {
                    ctx.resume();
                }

                const playClick = (startTime, duration, freq, gainVal) => {
                    const bufferSize = Math.floor(ctx.sampleRate * duration);
                    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
                    const data = buffer.getChannelData(0);
                    for (let i = 0; i < bufferSize; i++) {
                        data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.22));
                    }
                    const noise = ctx.createBufferSource();
                    noise.buffer = buffer;

                    const filter = ctx.createBiquadFilter();
                    filter.type = 'bandpass';
                    filter.frequency.setValueAtTime(freq, startTime);
                    filter.Q.setValueAtTime(2.5, startTime);

                    const gain = ctx.createGain();
                    gain.gain.setValueAtTime(gainVal, startTime);
                    gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);

                    noise.connect(filter);
                    filter.connect(gain);
                    gain.connect(ctx.destination);
                    noise.start(startTime);
                };

                const now = ctx.currentTime;
                playClick(now, 0.045, 2100, 0.9);
                playClick(now + 0.065, 0.055, 1450, 0.75);
                playClick(now + 0.16, 0.09, 950, 0.3);
            } catch (e) {
                console.log("Shutter audio skipped:", e);
            }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


# ---------------------------------------------------------
# ANALOG IMAGE PROCESSING ENGINE (NUMPY + OPENCV + PIL)
# ---------------------------------------------------------
def apply_film_stock(img_rgb: np.ndarray, stock: str) -> np.ndarray:
    """Applies custom LUT-style color curves and channel shifts."""
    img = img_rgb.astype(np.float32) / 255.0

    if stock == "Kodak Gold 200 (Warm Nostalgia)":
        img[:, :, 0] = np.clip(img[:, :, 0] * 1.12 + 0.03, 0, 1)
        img[:, :, 1] = np.clip(img[:, :, 1] * 1.04 + 0.02, 0, 1)
        img[:, :, 2] = np.clip(img[:, :, 2] * 0.86 + 0.04, 0, 1)
        img = np.clip((img - 0.5) * 1.08 + 0.52, 0, 1)

    elif stock == "Fujifilm Superia 400 (Crisp Greens)":
        img[:, :, 0] = np.clip(img[:, :, 0] * 0.96 + 0.01, 0, 1)
        img[:, :, 1] = np.clip(img[:, :, 1] * 1.08 + 0.02, 0, 1)
        img[:, :, 2] = np.clip(img[:, :, 2] * 1.05 + 0.03, 0, 1)
        img = np.clip((img - 0.5) * 1.15 + 0.50, 0, 1)

    elif stock == "Cinestill 800T (Tungsten Night)":
        img[:, :, 0] = np.clip(img[:, :, 0] * 0.94, 0, 1)
        img[:, :, 1] = np.clip(img[:, :, 1] * 1.02 + 0.02, 0, 1)
        img[:, :, 2] = np.clip(img[:, :, 2] * 1.18 + 0.04, 0, 1)
        highlights = np.maximum(img[:, :, 0] - 0.75, 0) * 1.8
        glow = cv2.GaussianBlur(highlights, (0, 0), sigmaX=12)
        img[:, :, 0] = np.clip(img[:, :, 0] + glow * 0.65, 0, 1)

    elif stock == "Ilford HP5 400 (Classic B&W)":
        gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
        gray = np.clip((gray - 0.5) * 1.28 + 0.51, 0.03, 0.97)
        img = np.stack([gray, gray, gray], axis=-1)

    elif stock == "Faded '70s Instant":
        img[:, :, 0] = np.clip(img[:, :, 0] * 1.08 + 0.07, 0, 1)
        img[:, :, 1] = np.clip(img[:, :, 1] * 0.98 + 0.06, 0, 1)
        img[:, :, 2] = np.clip(img[:, :, 2] * 0.84 + 0.08, 0, 1)
        img = np.clip((img - 0.5) * 0.85 + 0.53, 0, 1)

    return (img * 255).astype(np.uint8)


def add_film_grain(img_rgb: np.ndarray, intensity: float) -> np.ndarray:
    """Adds subtle, realistic 35mm luminance film grain (capped at 0.40)."""
    if intensity <= 0:
        return img_rgb
    clamped = min(intensity, 0.40)
    h, w, _ = img_rgb.shape
    rng = np.random.default_rng()
    small_noise = rng.normal(0, clamped * 38, (max(1, h // 2), max(1, w // 2)))
    grain = cv2.resize(small_noise, (w, h), interpolation=cv2.INTER_LINEAR)
    grain = np.repeat(grain[:, :, np.newaxis], 3, axis=2)
    noisy = np.clip(img_rgb.astype(np.float32) + grain, 0, 255)
    return noisy.astype(np.uint8)


def add_light_leak(img_rgb: np.ndarray, strength: float, leak_side: str) -> np.ndarray:
    """Simulates warm orange/magenta film door light leaks."""
    if strength <= 0 or leak_side == "None":
        return img_rgb
    h, w, _ = img_rgb.shape
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)

    if leak_side == "Left Edge Flare":
        mask = np.exp(-((xx - 0.02) ** 2) / 0.025) * (0.6 + 0.4 * np.sin(yy * np.pi))
    elif leak_side == "Right Corner Burn":
        mask = np.exp(-(((xx - 0.98) ** 2) / 0.03 + ((yy - 0.85) ** 2) / 0.18))
    else:
        mask = np.exp(-(((xx * 0.7 + yy * 0.5 - 0.15) ** 2) / 0.015))

    leak_layer = np.zeros_like(img_rgb, dtype=np.float32)
    leak_layer[:, :, 0] = 255 * mask * strength
    leak_layer[:, :, 1] = 115 * (mask ** 1.4) * strength
    leak_layer[:, :, 2] = 45 * (mask ** 2.0) * strength

    base = img_rgb.astype(np.float32) / 255.0
    leak = np.clip(leak_layer / 255.0, 0, 1)
    blended = 1.0 - (1.0 - base) * (1.0 - leak)
    return (np.clip(blended, 0, 1) * 255).astype(np.uint8)


def add_vignette(img_rgb: np.ndarray, strength: float) -> np.ndarray:
    """Applies optical lens falloff at the corners."""
    if strength <= 0:
        return img_rgb
    h, w, _ = img_rgb.shape
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    xx, yy = np.meshgrid(x, y)
    radius = np.sqrt(xx**2 + yy**2)
    mask = 1.0 - strength * np.clip((radius - 0.45) / 0.95, 0, 1) ** 1.8
    mask = mask[:, :, np.newaxis]
    return np.clip(img_rgb.astype(np.float32) * mask, 0, 255).astype(np.uint8)


def add_quartz_date_stamp(pil_img: Image.Image, date_text: str) -> Image.Image:
    """Burns a glowing 1990s orange LED date stamp onto the bottom-right corner."""
    if not date_text.strip():
        return pil_img
    img = pil_img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = img.size
    font_size = max(18, int(w * 0.032))
    try:
        font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), date_text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = (w - tw - int(w * 0.045), h - th - int(h * 0.045))

    for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.text((pos[0] + offset[0], pos[1] + offset[1]), date_text, font=font, fill=(255, 75, 0, 140))
    draw.text(pos, date_text, font=font, fill=(255, 165, 35, 240))

    return Image.alpha_composite(img, overlay).convert("RGB")


def develop_photo(
    raw_pil: Image.Image,
    stock: str,
    grain: float,
    leak_strength: float,
    leak_side: str,
    vignette: float,
    date_stamp: str,
    mirror: bool = False,
) -> Image.Image:
    """Full darkroom development pipeline."""
    img = ImageOps.exif_transpose(raw_pil).convert("RGB")
    if mirror:
        img = ImageOps.mirror(img)

    max_dim = 1400
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    arr = np.array(img)
    arr = apply_film_stock(arr, stock)
    arr = add_light_leak(arr, leak_strength, leak_side)
    arr = add_vignette(arr, vignette)
    arr = add_film_grain(arr, grain)

    developed = Image.fromarray(arr)
    if date_stamp:
        developed = add_quartz_date_stamp(developed, date_stamp)
    return developed


def render_photobooth_strip(
    frames: list[Image.Image],
    num_cuts: int,
    theme: str,
    caption: str,
) -> Image.Image:
    """Stitches 2, 3, or 4 developed frames into a vertical photobooth strip."""
    themes = {
        "Cream Paper": ("#F5E8D2", "#1B120F"),
        "Espresso Black": ("#1B120F", "#F5E8D2"),
        "Dark Mocha": ("#2A1C16", "#E8D3A5"),
        "Vanilla Gold": ("#E8D3A5", "#2A1C16"),
    }
    bg_hex, text_hex = themes.get(theme, ("#F5E8D2", "#1B120F"))

    frame_w, frame_h = 540, 405
    pad = 36
    gap = 24
    footer_h = 110

    strip_w = frame_w + pad * 2
    strip_h = pad + (frame_h * num_cuts) + (gap * (num_cuts - 1)) + footer_h

    strip = Image.new("RGB", (strip_w, strip_h), bg_hex)
    draw = ImageDraw.Draw(strip)

    for idx, frame in enumerate(frames[:num_cuts]):
        cropped = ImageOps.fit(frame, (frame_w, frame_h), method=Image.Resampling.LANCZOS)
        y_pos = pad + idx * (frame_h + gap)
        strip.paste(cropped, (pad, y_pos))

    try:
        title_font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 24)
        sub_font = ImageFont.truetype("DejaVuSansMono.ttf", 16)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    label = caption.strip() if caption.strip() else "EAKON 29 // PHOTOBOOTH"
    date_line = datetime.now().strftime(f"%Y.%m.%d • {num_cuts}-CUT ANALOG")

    y_text = pad + num_cuts * frame_h + (num_cuts - 1) * gap + 22
    draw.text((pad, y_text), label[:32], font=title_font, fill=text_hex)
    draw.text((pad, y_text + 36), date_line, font=sub_font, fill=text_hex)

    return strip


def pil_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_roll_zip(roll: list[dict]) -> bytes:
    """Bundles all captured shots in the current session into a single ZIP download."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, item in enumerate(roll):
            shot_num = len(roll) - i
            clean_label = item["label"].replace(" ", "_").replace("/", "-")
            zf.writestr(f"eakon29_{shot_num:02d}_{clean_label}.png", pil_to_bytes(item["image"]))
    return zip_buf.getvalue()


# ---------------------------------------------------------
# CENTERED EDITORIAL HEADER
# ---------------------------------------------------------
st.markdown(
    """
    <div class="brand-header">
        <h1 class="brand-title">Eakon 29</h1>
        <span class="brand-subtitle">Film Emulator and Photobooth</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# DYNAMIC LAYOUT: TWO INDEPENDENT STICKY RIGHT BOXES vs MINIMIZED STATES
# ---------------------------------------------------------
any_right_open = st.session_state.music_open or st.session_state.cam_menu_open

if any_right_open:
    col_main, col_right = st.columns([1.85, 0.95], gap="large")
    with col_right:
        st.markdown('<div class="sticky-right-marker" style="display:none;"></div>', unsafe_allow_html=True)

        if st.session_state.music_open:
            render_music_box()
        else:
            if st.button("◀ Listen to Music", key="open_music_btn", use_container_width=True):
                st.session_state.music_open = True
                st.rerun()

        if st.session_state.cam_menu_open:
            render_camera_settings_box()
        else:
            if st.button("◀ Choose Your Camera", key="open_cam_btn", use_container_width=True):
                st.session_state.cam_menu_open = True
                st.rerun()
else:
    _, col_main, col_dock = st.columns([0.30, 1.70, 0.30], gap="medium")
    with col_dock:
        st.markdown('<div class="sticky-right-marker" style="display:none;"></div>', unsafe_allow_html=True)
        if st.button("◀ Music", key="open_music_dock", help="Open Listen to Music", use_container_width=True):
            st.session_state.music_open = True
            st.rerun()
        if st.button("◀ Camera", key="open_cam_dock", help="Open Choose Your Camera", use_container_width=True):
            st.session_state.cam_menu_open = True
            st.rerun()

# Read active settings from session_state
film_stock = st.session_state.film_stock
picture_layout = st.session_state.picture_layout
grain_amt = st.session_state.grain_amt
vignette_amt = st.session_state.vignette_amt
leak_side = st.session_state.leak_side
leak_amt = st.session_state.leak_amt if leak_side != "None" else 0.0
custom_date = st.session_state.custom_date if st.session_state.show_date else ""
mirror_selfie = st.session_state.mirror_selfie
strip_theme = st.session_state.strip_theme
strip_caption = st.session_state.strip_caption

# Inject live film filter + grain CSS onto the Camera Shutter webcam preview
inject_live_camera_filter(
    stock=film_stock,
    grain=grain_amt,
    vignette=vignette_amt,
    leak_side=leak_side,
    leak_amt=leak_amt,
    date_stamp=custom_date,
    mirror=mirror_selfie,
)

# --- MAIN CAMERA, SUPER 8, PREVIEW & GALLERY AREA ---
with col_main:
    input_source = st.tabs(["📸 Camera Shutter", "🎥 Super 8 Camcorder", "📂 Upload Pictures"])

    captured_pil = None
    capture_signature = None

    with input_source[0]:
        cam_photo = st.camera_input(
            "Camera Shutter",
            key=f"webcam_{st.session_state.cam_key}",
            label_visibility="collapsed",
        )
        if cam_photo is not None:
            captured_pil = Image.open(cam_photo)
            capture_signature = ("cam", st.session_state.cam_key, cam_photo.name, cam_photo.size)

    with input_source[1]:
        render_super8_camcorder(
            stock=film_stock,
            grain=grain_amt,
            vignette=vignette_amt,
            leak_side=leak_side,
            leak_amt=leak_amt,
            date_stamp=custom_date,
            mirror=mirror_selfie,
        )

    with input_source[2]:
        uploaded_file = st.file_uploader(
            "Drop a JPG/PNG/WEBP photo to develop",
            type=["jpg", "jpeg", "png", "webp"],
        )
        if uploaded_file is not None:
            captured_pil = Image.open(uploaded_file)
            capture_signature = ("upload", uploaded_file.name, uploaded_file.size)

    if capture_signature is not None and capture_signature != st.session_state.last_capture_sig:
        st.session_state.last_capture_sig = capture_signature
        trigger_shutter_effect()

    st.divider()
    st.subheader("Preview Your Photo")

    developed_img = None
    if captured_pil is not None:
        developed_img = develop_photo(
            raw_pil=captured_pil,
            stock=film_stock,
            grain=grain_amt,
            leak_strength=leak_amt,
            leak_side=leak_side,
            vignette=vignette_amt,
            date_stamp=custom_date,
            mirror=mirror_selfie,
        )
        st.image(developed_img, use_container_width=True, caption=f"Shot on {film_stock}")
    else:
        st.markdown(
            """
            <div class="film-card" style="text-align:center;">
                <p style="margin:0;">Snap a photo with your webcam or upload an image above to preview it here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # SINGLE FRAME ACTIONS
    if picture_layout == "Single Frame":
        if developed_img is not None:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🎞️ Save to Gallery", use_container_width=True):
                    st.session_state.film_roll.insert(
                        0,
                        {
                            "image": developed_img,
                            "label": film_stock.split(" (")[0],
                            "time": datetime.now().strftime("%H%M%S%f"),
                        },
                    )
                    st.toast("Saved frame to Captured Shots!", icon="🎞️")
                    st.rerun()
            with b2:
                st.download_button(
                    label="⬇️ Download (.PNG)",
                    data=pil_to_bytes(developed_img),
                    file_name=f"eakon29_{datetime.now().strftime('%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True,
                )

    # PHOTOSTRIP TRAY (ALWAYS VISIBLE IN 2-CUT / 3-CUT / 4-CUT MODE)
    else:
        target_cuts = int(picture_layout.split("-")[0])
        count = len(st.session_state.booth_frames)
        st.info(f"🎞️ {picture_layout} Tray: **{count} / {target_cuts} frames** captured")

        if count > 0:
            thumb_cols = st.columns(target_cuts)
            for i, frame in enumerate(st.session_state.booth_frames):
                with thumb_cols[i]:
                    st.image(frame, use_container_width=True, caption=f"Cut #{i+1}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                f"➕ Add Frame ({count}/{target_cuts})",
                disabled=(developed_img is None or count >= target_cuts),
                use_container_width=True,
            ):
                st.session_state.booth_frames.append(developed_img)
                st.session_state.cam_key += 1
                st.rerun()
        with c2:
            if st.button("🗑️ Reset Strip", use_container_width=True):
                st.session_state.booth_frames = []
                st.session_state.cam_key += 1
                st.rerun()

        if len(st.session_state.booth_frames) == target_cuts:
            final_strip = render_photobooth_strip(
                st.session_state.booth_frames,
                num_cuts=target_cuts,
                theme=strip_theme,
                caption=strip_caption,
            )
            st.image(final_strip, width=340, caption=f"Your {picture_layout}")

            s1, s2 = st.columns(2)
            with s1:
                if st.button("🎞️ Save Strip to Gallery", use_container_width=True):
                    st.session_state.film_roll.insert(
                        0,
                        {
                            "image": final_strip,
                            "label": f"{picture_layout} • {film_stock.split(' (')[0]}",
                            "time": datetime.now().strftime("%H%M%S%f"),
                        },
                    )
                    st.toast(f"Saved {picture_layout} to Captured Shots!", icon="🎞️")
                    st.rerun()
            with s2:
                st.download_button(
                    label=f"⬇️ Download {picture_layout} (.PNG)",
                    data=pil_to_bytes(final_strip),
                    file_name=f"eakon29_{target_cuts}cut_{datetime.now().strftime('%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True,
                )

    # ---------------------------------------------------------
    # CAPTURED SHOTS GALLERY (INSIDE LEFT COLUMN SO RIGHT PANEL STAYS PINNED)
    # ---------------------------------------------------------
    if st.session_state.film_roll:
        st.divider()
        gal_head, gal_zip = st.columns([2.6, 1.2])
        with gal_head:
            st.subheader("Captured Shots")
        with gal_zip:
            st.download_button(
                label="📦 Download All (.ZIP)",
                data=build_roll_zip(st.session_state.film_roll),
                file_name=f"eakon29_session_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
                use_container_width=True,
            )

        cols = st.columns(3)
        for idx, item in enumerate(st.session_state.film_roll):
            with cols[idx % 3]:
                st.image(item["image"], use_container_width=True)
                st.caption(f"#{len(st.session_state.film_roll) - idx:02d} • {item['label']}")
                dl_col, del_col = st.columns([3.2, 1], gap="small")
                with dl_col:
                    st.download_button(
                        "Download",
                        data=pil_to_bytes(item["image"]),
                        file_name=f"eakon29_shot_{len(st.session_state.film_roll) - idx:02d}.png",
                        mime="image/png",
                        key=f"dl_{idx}_{item['time']}",
                        use_container_width=True,
                    )
                with del_col:
                    if st.button(
                        "🗑️",
                        key=f"del_{idx}_{item['time']}",
                        help="Delete from gallery",
                        use_container_width=True,
                    ):
                        st.session_state.film_roll.pop(idx)
                        st.toast("Removed shot from gallery", icon="🗑️")
                        st.rerun()