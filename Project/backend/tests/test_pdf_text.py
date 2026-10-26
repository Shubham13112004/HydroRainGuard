"""
Tests for the HarfBuzz-backed PDF text layer.

The point of these tests is that Devanagari is *shaped*, not merely
mapped: conjuncts must collapse into single glyphs, the I-matra must be
reordered in front of its consonant, and the reph must be emitted as a
zero-advance mark. A renderer that only walks codepoints would fail
every one of these.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

from services.text_shaper import (
    DEVA_REGULAR, LATIN_REGULAR, HAS_FONTS,
    shape, string_width, needs_shaping, has_devanagari,
    _prepare, _split_runs,
    ShapedParagraph, P,
)
from services import pdf_report
from models.schemas import AssessmentRequest


# ------------------------------------------------------------ test app wiring

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _purge_backend_modules():
    """Allow each app fixture to build its own SQLAlchemy engine."""
    stale = [
        name
        for name, mod in list(sys.modules.items())
        if getattr(mod, "__file__", None)
        and os.path.abspath(mod.__file__).startswith(BACKEND_DIR)
    ]
    for name in stale:
        sys.modules.pop(name, None)


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient with a throwaway database and normal startup lifecycle."""
    db_file = tmp_path_factory.mktemp("pdf_db") / "test.db"

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")
        mp.setenv("ENVIRONMENT", "development")
        _purge_backend_modules()

        import main

        with TestClient(main.app) as c:
            yield c

        _purge_backend_modules()


# ------------------------------------------------------------------ shaping

def _names(text, path=DEVA_REGULAR):
    return shape(text, path).glyphs


def test_conjuncts_collapse_to_one_glyph():
    assert _names("क्ष") == ["kassadeva"]
    assert _names("ज्ञ") == ["janyadeva"]
    assert _names("त्र") == ["taradeva"]
    assert _names("श्र") == ["sharadeva"]


def test_i_matra_is_reordered_before_its_consonant():
    """पि is stored as प + ि but drawn as ि + प."""
    assert _names("पि") == ["ivowelsign03deva", "padeva"]


def test_reph_is_a_zero_advance_mark_after_the_cluster():
    run = shape("विदर्भ", DEVA_REGULAR)
    assert "rephdeva" in run.glyphs
    idx = run.glyphs.index("rephdeva")
    assert run.positions[idx][2] == 0


def test_half_form_substitution():
    """हिन्दी uses a pre-base half form for न."""
    assert "naprehalfdeva" in _names("हिन्दी")


def test_no_notdef_for_devanagari():
    for text in ["क्ष", "ज्ञ", "हिन्दी", "मराठी", "पुनर्भरण", "विदर्भ", "श्री"]:
        assert ".notdef" not in _names(text), text


def test_latin_does_not_need_shaping():
    assert not needs_shaping("Rainwater harvesting 123 mm")
    assert needs_shaping("पावसाचे पाणी")
    assert has_devanagari("पुणे")
    assert not has_devanagari("Pune")


def test_advance_width_scales_with_size():
    w10 = string_width("पुणे", 10)
    w20 = string_width("पुणे", 20)
    assert w20 == pytest.approx(w10 * 2, rel=1e-6)
    assert w10 > 0


# ------------------------------------------------------- font fallback

def test_uncovered_characters_are_substituted():
    # U+2192 is not in Noto Sans; it must not survive into the PDF.
    assert "→" not in _prepare("a → b", False)
    assert "->" in _prepare("a → b", False)


def test_covered_characters_are_left_alone():
    assert _prepare("पुणे 25°C ₹100", False) == "पुणे 25°C ₹100"


def test_runs_split_by_font_coverage():
    runs = _split_runs("पुणे (Pune) 25°C", False)
    assert len(runs) > 1
    fonts = {p for _, p in runs}
    assert DEVA_REGULAR in fonts and LATIN_REGULAR in fonts
    assert "".join(t for t, _ in runs) == "पुणे (Pune) 25°C"


# --------------------------------------------------------------- flowable

def test_shaped_paragraph_measures_and_splits():
    para = P("word " * 200, size=9)
    w, h = para.wrap(200, 10000)
    assert w == 200
    assert h > 9
    parts = para.split(200, 100)
    assert len(parts) >= 2
    assert all(isinstance(p, ShapedParagraph) for p in parts)


def test_shaped_paragraph_reports_zero_for_empty():
    p = P("", size=9)
    w, h = p.wrap(200, 100)
    assert w == 200
    assert h >= 0


# ---------------------------------------------------------------- report

@pytest.fixture(scope="module")
def sample_pdf(client):
    payload = dict(
        name="श्रीमती सुनीता पाटील",
        location="कोल्हापूर, महाराष्ट्र",
        latitude=16.7050,
        longitude=74.2433,
        num_people=6,
        roof_type="RCC",
        roof_area=150.0,
        open_space_area=80.0,
        soil_type="LOAMY",
        groundwater_depth=12.0,
    )
    r = client.post("/api/assess", json=payload)
    assert r.status_code == 200, r.text[:800]
    return client.get(f"/api/report/{r.json()['assessment_id']}").content


def test_report_generates_valid_pdf(sample_pdf):
    assert sample_pdf[:5] == b"%PDF-"
    assert sample_pdf.rstrip().endswith(b"%%EOF")
    assert len(sample_pdf) > 10_000


def test_report_embeds_only_the_latin_face(sample_pdf):
    """
    Noto Sans is embedded because Latin runs use drawString (so they
    stay copyable). Devanagari is drawn as vector outlines, so the
    Devanagari face itself never has to be embedded -- smaller PDF, and
    no OFL font is shipped inside the document.
    """
    assert b"NotoSans" in sample_pdf
    assert b"NotoSansDevanagari" not in sample_pdf


def test_devanagari_adds_vector_outline_data(client):
    """Same inputs, Devanagari name -> a bigger file (glyph outlines)."""
    base = dict(
        latitude=16.7050, longitude=74.2433, num_people=6,
        roof_type="RCC", roof_area=150.0, open_space_area=80.0,
        soil_type="LOAMY", groundwater_depth=12.0,
    )

    def size(name, location):
        r = client.post("/api/assess", json=dict(base, name=name,
                                                 location=location))
        assert r.status_code == 200
        return len(client.get(f"/api/report/{r.json()['assessment_id']}").content)

    latin = size("Sunita Patil", "Kolhapur, Maharashtra")
    deva = size("सुनीता पाटील", "कोल्हापूर, महाराष्ट्र")
    assert deva > latin


def test_report_has_multiple_pages(sample_pdf):
    assert raw_page_count(sample_pdf) >= 2


def raw_page_count(data: bytes) -> int:
    return data.count(b"/Type /Page\n") or data.count(b"/Type/Page") or 1


def test_report_is_deterministic_in_size(client):
    """Two reports for the same inputs should be within 5% of each other."""
    payload = dict(
        name="Test", location="Pune", latitude=18.52, longitude=73.85,
        num_people=4, roof_type="RCC", roof_area=100.0,
        open_space_area=50.0, soil_type="SANDY", groundwater_depth=15.0,
    )
    sizes = []
    for _ in range(2):
        r = client.post("/api/assess", json=payload)
        assert r.status_code == 200
        sizes.append(len(client.get(f"/api/report/{r.json()['assessment_id']}").content))
    assert abs(sizes[0] - sizes[1]) / max(sizes) < 0.05
