import glob, os, cv2, yaml, numpy as np
from PIL import Image
import pytesseract
from conditions import find_template_multiscale

CFG = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
COND = CFG["condition"]; TPATH = COND.get("template_path")
T = cv2.imread(TPATH) if TPATH else None
CONF = float(COND.get("confidence", 0.85))
MS = COND.get("multiscale", {"enabled": False})
SCALES = MS.get("scales", [1.0]) if MS.get("enabled", False) else [1.0]
PICK = MS.get("pick", "best")

PSM = int(COND.get("ocr_psm", 6)); CS = bool(COND.get("case_sensitive", False))
QUERY = COND.get("text_query", "")

def ocr_hit(img):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(Image.fromarray(rgb), config=f"--psm {PSM}")
    return (QUERY in text) if CS else (QUERY.lower() in text.lower())

def predict(img):
    if COND["type"] == "template":
        hit = find_template_multiscale(img, T, CONF, SCALES, PICK)
        return (hit is not None, hit)
    else:
        ok = ocr_hit(img)
        return (ok, None)

def eval_dir(path, label, outdir):
    os.makedirs(outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(path, "*.png")))
    tp=fp=tn=fn=0
    for f in files:
        img = cv2.imread(f)
        ok, info = predict(img)
        if ok and label=="pos":
            tp+=1
        elif ok and label=="neg":
            fp+=1
            cv2.imwrite(os.path.join(outdir, "FP_"+os.path.basename(f)), img)
        elif (not ok) and label=="neg":
            tn+=1
        else:
            fn+=1
            if info and COND["type"]=="template":
                x,y,w,h,score,scale = info
                cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,255),2)
            cv2.imwrite(os.path.join(outdir, "FN_"+os.path.basename(f)), img)
    return tp,fp,tn,fn

tp,fp,tn,fn = 0,0,0,0
a=eval_dir("samples/pos","pos","report/pos"); tp+=a[0]; fp+=a[1]; tn+=a[2]; fn+=a[3]
b=eval_dir("samples/neg","neg","report/neg"); tp+=b[0]; fp+=b[1]; tn+=b[2]; fn+=b[3]

precision = tp/(tp+fp) if (tp+fp) else 0.0
recall    = tp/(tp+fn) if (tp+fn) else 0.0
print(f"TP={tp} FP={fp} TN={tn} FN={fn}")
print(f"Precision={precision:.3f}  Recall={recall:.3f}")
print("Annotated misses in ./report/")
