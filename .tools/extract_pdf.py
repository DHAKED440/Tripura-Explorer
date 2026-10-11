import glob
from pypdf import PdfReader
path = glob.glob(r"F:\Tripura Torisem Explorere\flow\*.pdf")[0]
reader = PdfReader(path)
out = []
for i, page in enumerate(reader.pages, start=1):
    out.append(f"\n===== PAGE {i} =====\n")
    out.append(page.extract_text() or "")
text = "".join(out)
open(".tools/pdf.txt", "w", encoding="utf-8").write(text)
print("pages", len(reader.pages), "chars", len(text))
