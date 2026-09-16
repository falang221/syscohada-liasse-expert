"""Tests for the AI commentary service.

The value returned here is rendered in the liasse PDF under "NOTE DE SYNTHÈSE
DE LA DIRECTION" - a document handed to the client. No error text, no raw
exception and no empty section may ever reach it.
"""

import pytest
from jinja2 import Environment, FileSystemLoader

from app.services import ai_service
from app.services.financial_engine import compute_financial_statements

STATEMENTS = {
    "resultat_produit": {"Chiffre d'affaires": {"net": 1_000_000, "net_n_1": 800_000}},
    "resultat_charge": {"Achats": {"net": 600_000, "net_n_1": 500_000}},
}


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


def _fake_client(response=None, error=None):
    class _Chat:
        def complete(self, **kwargs):
            _Chat.last_kwargs = kwargs
            if error:
                raise error
            return _FakeResponse(response)

    class _Client:
        def __init__(self, api_key=None):
            self.chat = _Chat()

    return _Client


@pytest.fixture
def with_key(monkeypatch):
    monkeypatch.setattr(ai_service, "MISTRAL_API_KEY", "test-key")


@pytest.mark.unit
class TestModeleConfigurable:
    def test_defaut(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_MODEL", raising=False)
        assert ai_service.get_mistral_model() == "mistral-large-latest"

    def test_surcharge_par_env(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_MODEL", "ministral-14b-latest")
        assert ai_service.get_mistral_model() == "ministral-14b-latest"

    def test_env_vide_retombe_sur_le_defaut(self, monkeypatch):
        monkeypatch.setenv("MISTRAL_MODEL", "")
        assert ai_service.get_mistral_model() == "mistral-large-latest"

    def test_le_modele_est_transmis_a_lapi(self, monkeypatch, with_key):
        monkeypatch.setenv("MISTRAL_MODEL", "ministral-14b-latest")
        client_cls = _fake_client(response="Note.")
        monkeypatch.setattr(ai_service, "Mistral", client_cls)

        ai_service.generate_financial_commentary(STATEMENTS)

        assert client_cls().chat.last_kwargs["model"] == "ministral-14b-latest"


@pytest.mark.unit
class TestAucuneFuiteDansLePdf:
    def test_erreur_api_retourne_none(self, monkeypatch, with_key):
        """A 429 must not become the client's management note."""
        boom = Exception('{"message":"Rate limit exceeded","code":"1300"}')
        monkeypatch.setattr(ai_service, "Mistral", _fake_client(error=boom))

        assert ai_service.generate_financial_commentary(STATEMENTS) is None

    def test_cle_absente_retourne_none(self, monkeypatch):
        monkeypatch.setattr(ai_service, "MISTRAL_API_KEY", "")
        assert ai_service.generate_financial_commentary(STATEMENTS) is None

    def test_reponse_vide_retourne_none(self, monkeypatch, with_key):
        monkeypatch.setattr(ai_service, "Mistral", _fake_client(response="   "))
        assert ai_service.generate_financial_commentary(STATEMENTS) is None

    def test_reponse_none_retourne_none(self, monkeypatch, with_key):
        monkeypatch.setattr(ai_service, "Mistral", _fake_client(response=None))
        assert ai_service.generate_financial_commentary(STATEMENTS) is None

    def test_lexception_est_journalisee_pas_retournee(self, monkeypatch, with_key, caplog):
        boom = Exception("SECRET-DETAIL-429")
        monkeypatch.setattr(ai_service, "Mistral", _fake_client(error=boom))

        with caplog.at_level("ERROR"):
            result = ai_service.generate_financial_commentary(STATEMENTS)

        assert result is None
        assert "SECRET-DETAIL-429" in caplog.text, "le detail doit rester dans les logs"


@pytest.mark.unit
class TestCasNominal:
    def test_commentaire_retourne_et_nettoye(self, monkeypatch, with_key):
        monkeypatch.setattr(
            ai_service, "Mistral", _fake_client(response="  Exercice satisfaisant.  ")
        )
        assert ai_service.generate_financial_commentary(STATEMENTS) == "Exercice satisfaisant."


@pytest.mark.unit
class TestRenduPdf:
    """The section must disappear entirely rather than show an error."""

    @pytest.fixture(scope="class")
    def template(self):
        env = Environment(loader=FileSystemLoader("app/templates"))
        return env.get_template("liasse_template.html")

    def _render(self, template, commentary):
        # Build a real statements payload: the template formats TAFIRE fields
        # a hand-rolled dict would not carry.
        statements = compute_financial_statements(
            [
                {"compte": "521", "debit": 100_000, "credit": 0},
                {"compte": "101", "debit": 0, "credit": 100_000},
            ]
        )
        return template.render(
            statements=statements, client_info={},
            ai_commentary=commentary, exercice="2026",
        )

    def test_section_absente_quand_none(self, template):
        html = self._render(template, None)
        assert "NOTE DE SYNTHÈSE DE LA DIRECTION" not in html

    def test_section_presente_quand_commentaire(self, template):
        html = self._render(template, "Exercice satisfaisant.")
        assert "NOTE DE SYNTHÈSE DE LA DIRECTION" in html
        assert "Exercice satisfaisant." in html

    def test_aucun_message_derreur_ne_sort(self, monkeypatch, with_key, template):
        """End to end: a failing API leaves no trace in the document."""
        monkeypatch.setattr(
            ai_service, "Mistral", _fake_client(error=Exception("Rate limit exceeded"))
        )
        commentary = ai_service.generate_financial_commentary(STATEMENTS)
        html = self._render(template, commentary)

        for interdit in ["Rate limit", "erreur", "Erreur", "Exception"]:
            assert interdit not in html
