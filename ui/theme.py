import ttkbootstrap as tb

# chnage if you dont like it
PALETTE = {
    "bg":     "#1f1f1c",  
    "card":   "#262622",
    "text":   "#e9e4d6",
    "muted":  "#bdb6a3",
    "accent": "#d9c7a3",
    "accent2":"#b28b67",
    "logbg":  "#21201d",
}

def init_style():

    style = tb.Style("journal")
    style.configure("TFrame", background=PALETTE["bg"])
    style.configure("Card.TFrame", background=PALETTE["card"])
    style.configure("TLabel", background=PALETTE["card"], foreground=PALETTE["text"])
    style.configure("Title.TLabel", background=PALETTE["card"], foreground=PALETTE["accent"], font=("Segoe UI Semibold", 16))
    style.configure("Muted.TLabel", background=PALETTE["card"], foreground=PALETTE["muted"])
    return style, PALETTE
