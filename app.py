import io
import zipfile
import base64
import hashlib
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PyPDF2 import PdfReader, PdfWriter

# --- Simple brand color (Sam's blue) ---
SAMS_BLUE_RGB = (27/255.0, 75/255.0, 155/255.0)

st.set_page_config(page_title="Minimal MAP PDF Generator", page_icon="🗂️", layout="centered")
st.title("🗂️ Minimal MAP PDF Generator")
st.caption("Fillable + Locked Sample + Locked Blank • Bookmarks • Metadata • ZIP + checksums")

# ---------- tiny helpers ----------
def _header(c, title, page_w=LETTER[0], page_h=LETTER[1]):
    c.setFillColorRGB(*SAMS_BLUE_RGB)
    c.rect(0, page_h - 0.6*inch, page_w, 0.6*inch, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0.75*inch, page_h - 0.4*inch, title)

def _add_meta_and_bookmarks(pdf_bytes, title, subject, keywords, version, internal_note, section_titles):
    """Return new PDF bytes with metadata + bookmarks using PyPDF2 only."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    meta = {
        "/Title": title,
        "/Author": "Minimal App",
        "/Subject": subject,
        "/Keywords": keywords,
        "/Version": version,
        "/InternalNote": internal_note,
        "/Producer": "ReportLab + PyPDF2 (Minimal)",
    }
    writer.add_metadata(meta)

    num_pages = len(writer.pages)
    labels = list(section_titles)[:num_pages] + [f"Page {i+1}" for i in range(len(section_titles), num_pages)]
    for i in range(num_pages):
        # Newer PyPDF2
        try:
            writer.add_outline_item(labels[i], i)
        except Exception:
            # Older PyPDF2
            try:
                writer.addBookmark(labels[i], i)
            except Exception:
                pass

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

# ---------- PDF makers (simple) ----------
def make_fillable_pdf_bytes(doc_title, version, internal_note):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    page_w, page_h = LETTER

    _header(c, doc_title, page_w, page_h)
    c.setFillColor(colors.black); c.setFont("Helvetica", 12)
    c.drawString(0.8*inch, page_h - 1.2*inch, "MAP Brief — Fillable")
    c.setFont("Helvetica", 10)
    c.drawString(0.8*inch, page_h - 1.5*inch, f"Version: {version}")

    form = c.acroForm
    border_color = colors.Color(*SAMS_BLUE_RGB)

    # Name
    c.drawString(0.8*inch, page_h - 2.2*inch, "Name:")
    form.textfield(
        name="Name", tooltip="Enter your full name",
        x=1.4*inch, y=page_h - 2.35*inch, width=3.5*inch, height=0.3*inch,
        borderStyle="solid", borderColor=border_color, textColor=colors.black, forceBorder=True,
    )
    # Title
    c.drawString(0.8*inch, page_h - 2.7*inch, "Title:")
    form.textfield(
        name="Title", tooltip="Enter your job title",
        x=1.4*inch, y=page_h - 2.85*inch, width=3.5*inch, height=0.3*inch,
        borderStyle="solid", borderColor=border_color, textColor=colors.black, forceBorder=True,
    )
    # Comments (multiline via fieldFlags STRING)
    c.drawString(0.8*inch, page_h - 3.2*inch, "Comments:")
    form.textfield(
        name="Comments", tooltip="Enter additional comments (multiline)",
        x=0.8*inch, y=page_h - 6.0*inch, width=6.9*inch, height=2.6*inch,
        borderStyle="solid", borderColor=border_color, textColor=colors.black, forceBorder=True,
        fieldFlags="multiline",
    )

    # A couple of extra pages to demonstrate bookmarks
    for title, lines in [
        ("Section 1 — Overview", ["Goal & context.", "Use brand color consistently."]),
        ("Section 2 — Submission", ["Review entries, then submit/export as needed."]),
    ]:
        c.showPage()
        _header(c, title, page_w, page_h)
        c.setFillColor(colors.black); c.setFont("Helvetica", 11)
        y = page_h - 1.2*inch
        for line in lines:
            c.drawString(0.8*inch, y, line); y -= 14

    c.setTitle(doc_title); c.setAuthor("Minimal App")
    c.setSubject("MAP Brief (Fillable)"); c.setKeywords(["MAP","Brief","Fillable"])
    c.save()

    base = buf.getvalue()
    return _add_meta_and_bookmarks(
        base, doc_title, "MAP Brief (Fillable)", "MAP;Brief;Fillable",
        version, internal_note,
        ["Cover", "Section 1 — Overview", "Section 2 — Submission"]
    )

def make_locked_sample_pdf_bytes(doc_title, version, approved_name, approved_title, approved_date, internal_note):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    page_w, page_h = LETTER

    _header(c, doc_title, page_w, page_h)
    c.setFillColor(colors.black); c.setFont("Helvetica", 12)
    c.drawString(0.8*inch, page_h - 1.2*inch, "MAP Brief — Sample (Locked)")
    c.setFont("Helvetica", 10)
    y = page_h - 1.7*inch
    for line in [
        "Name: Jane Sample",
        "Title: Senior Analyst",
        "Comments: Pre-filled sample text demonstrating the final appearance.",
    ]:
        c.drawString(0.8*inch, y, line); y -= 14

    c.setStrokeColorRGB(*SAMS_BLUE_RGB)
    c.rect(0.8*inch, page_h - 3.6*inch - 0.8*inch, 6.9*inch, 0.8*inch, fill=False, stroke=True)
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11)
    c.drawString(0.9*inch, page_h - 3.6*inch - 0.25*inch,
                 f"Approved by: {approved_name} | {approved_title} | {approved_date}")

    c.showPage()
    _header(c, "Finalization", page_w, page_h)
    c.setFillColor(colors.black); c.setFont("Helvetica", 11)
    c.drawString(0.8*inch, page_h - 1.2*inch, "This sample is flattened and intended for distribution.")

    c.setTitle(doc_title); c.setAuthor("Minimal App")
    c.setSubject("MAP Brief (Locked Sample)"); c.setKeywords(["MAP","Brief","Sample","Locked"])
    c.save()

    base = buf.getvalue()
    return _add_meta_and_bookmarks(
        base, doc_title, "MAP Brief (Locked Sample)", "MAP;Brief;Sample;Locked",
        version, internal_note,
        ["Cover", "Finalization"]
    )

def make_locked_blank_pdf_bytes(doc_title, version, internal_note):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    page_w, page_h = LETTER

    _header(c, doc_title, page_w, page_h)
    c.setFillColor(colors.black); c.setFont("Helvetica", 12)
    c.drawString(0.8*inch, page_h - 1.2*inch, "MAP Brief — Blank (Locked)")

    c.setFont("Helvetica", 10)
    c.drawString(0.8*inch, page_h - 1.6*inch, "Fields (visual only on this version):")
    c.drawString(0.8*inch, page_h - 1.9*inch, "• Name   • Title   • Comments")

    c.setStrokeColorRGB(*SAMS_BLUE_RGB)
    c.rect(1.4*inch, page_h - 2.35*inch, 3.5*inch, 0.3*inch, fill=False, stroke=True)  # Name
    c.rect(1.4*inch, page_h - 2.85*inch, 3.5*inch, 0.3*inch, fill=False, stroke=True)  # Title
    c.rect(0.8*inch,  page_h - 6.0*inch, 6.9*inch, 2.6*inch, fill=False, stroke=True)  # Comments

    c.showPage()
    _header(c, "Layout Reference", page_w, page_h)
    c.setFillColor(colors.black); c.setFont("Helvetica", 11)
    c.drawString(0.8*inch, page_h - 1.2*inch, "Matches the fillable layout but flattened (no form fields).")

    c.setTitle(doc_title); c.setAuthor("Minimal App")
    c.setSubject("MAP Brief (Locked Blank)"); c.setKeywords(["MAP","Brief","Blank","Locked"])
    c.save()

    base = buf.getvalue()
    return _add_meta_and_bookmarks(
        base, doc_title, "MAP Brief (Locked Blank)", "MAP;Brief;Blank;Locked",
        version, internal_note,
        ["Cover", "Layout Reference"]
    )

# ---------- ZIP + checksum ----------
def make_zip(fillable, sample, blank):
    zbio = io.BytesIO()
    with zipfile.ZipFile(zbio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MAP_Brief_Fillable.pdf", fillable)
        zf.writestr("MAP_Brief_Sample_Locked.pdf", sample)
        zf.writestr("MAP_Brief_Blank_Locked.pdf", blank)
    return zbio.getvalue()

def sha256_hex_b64(b: bytes):
    digest = hashlib.sha256(b).digest()
    return digest.hex(), base64.b64encode(digest).decode("ascii")

# ---------- UI ----------
with st.sidebar:
    st.header("Settings (minimal)")
    title = st.text_input("Document Title", value="MAP Brief")
    version = st.text_input("Version", value="1.0")
    internal_note = st.text_input("Hidden Internal Note", value="Generated by minimal app.")
    st.subheader("Approved By (Sample PDF)")
    appr_name = st.text_input("Name", value="John Doe")
    appr_title = st.text_input("Title", value="Manager, Operations")
    appr_date = st.text_input("Date", value=datetime.now().strftime("%Y-%m-%d"))

col1, col2 = st.columns(2)
generate = col1.button("Generate PDFs & ZIP", type="primary")
reset = col2.button("Reset")
if reset:
    st.rerun()

if generate:
    with st.spinner("Generating..."):
        fillable = make_fillable_pdf_bytes(title, version, internal_note)
        sample   = make_locked_sample_pdf_bytes(title, version, appr_name, appr_title, appr_date, internal_note)
        blank    = make_locked_blank_pdf_bytes(title, version, internal_note)
        zbytes   = make_zip(fillable, sample, blank)
        hex_d, b64_d = sha256_hex_b64(zbytes)

    st.success("Done!")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Fillable PDF", data=fillable, file_name="MAP_Brief_Fillable.pdf", mime="application/pdf")
        st.download_button("⬇️ Locked Sample PDF", data=sample, file_name="MAP_Brief_Sample_Locked.pdf", mime="application/pdf")
    with c2:
        st.download_button("⬇️ Locked Blank PDF", data=blank, file_name="MAP_Brief_Blank_Locked.pdf", mime="application/pdf")
        st.download_button("⬇️ ZIP Package", data=zbytes, file_name="MAP_Briefs_Package.zip", mime="application/zip")

    st.subheader("ZIP SHA-256")
    st.code(f"Hex:    {hex_d}\nBase64: {b64_d}", language="text")
