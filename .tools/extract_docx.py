import zipfile, re, sys, glob, os
path = glob.glob(r"F:\Tripura Torisem Explorere\*.docx")[0]
print("FILE:", path)
z = zipfile.ZipFile(path)
xml = z.read("word/document.xml").decode("utf-8")
xml = xml.replace("</w:p>", "\n")
xml = xml.replace("</w:tc>", " | ")
xml = xml.replace("</w:tr>", "\n")
text = re.sub(r"<[^>]+>", "", xml)
import html
text = html.unescape(text)
out = "\n".join(line.rstrip() for line in text.splitlines())
open(".tools/docx.txt","w",encoding="utf-8").write(out)
print(len(out))
