# frontend/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_user(username="testuser", password="testpass123", **kwargs):
    return User.objects.create_user(username=username, password=password, **kwargs)


def make_superuser(username="superadmin", password="superpass123"):
    return User.objects.create_superuser(username=username, password=password)


# ─────────────────────────────────────────────
# LoginView
# ─────────────────────────────────────────────

class LoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("frontend:login")
        self.user = make_user()

    def test_get_affiche_formulaire(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Connexion")

    def test_get_utilisateur_connecte_redirige_dashboard(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertRedirects(resp, reverse("frontend:dashboard"))

    def test_post_identifiants_corrects_connecte_et_redirige(self):
        resp = self.client.post(self.url, {
            "username": "testuser",
            "password": "testpass123",
            "next": "/app/",
        })
        self.assertRedirects(resp, "/app/")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_post_mauvais_mot_de_passe_affiche_erreur(self):
        resp = self.client.post(self.url, {
            "username": "testuser",
            "password": "mauvais",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Identifiant ou mot de passe incorrect")

    def test_post_utilisateur_inexistant_affiche_erreur(self):
        resp = self.client.post(self.url, {
            "username": "inconnu",
            "password": "nimporte",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Identifiant ou mot de passe incorrect")

    def test_post_compte_desactive_affiche_erreur(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(self.url, {
            "username": "testuser",
            "password": "testpass123",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "sactiv")

    def test_next_externe_redirige_vers_app(self):
        """Un next vers un domaine externe doit etre ignore (securite)."""
        resp = self.client.post(self.url, {
            "username": "testuser",
            "password": "testpass123",
            "next": "http://evil.com/",
        })
        self.assertRedirects(resp, "/app/")


# ─────────────────────────────────────────────
# LogoutView
# ─────────────────────────────────────────────

class LogoutViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("frontend:logout")
        self.user = make_user()

    def test_post_deconnecte_et_redirige(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url)
        self.assertRedirects(resp, "/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_get_redirige_sans_deconnecter(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertRedirects(resp, reverse("frontend:dashboard"))
        self.assertIn("_auth_user_id", self.client.session)


# ─────────────────────────────────────────────
# ProfilView
# ─────────────────────────────────────────────

class ProfilViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("frontend:profil")
        self.user = make_user(password="ancien123")

    def test_get_necessite_connexion(self):
        resp = self.client.get(self.url)
        self.assertRedirects(resp, f"/app/login/?next={self.url}")

    def test_get_affiche_page_profil(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_post_changement_mot_de_passe_reussi(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {
            "password": "nouveau456",
            "password2": "nouveau456",
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("nouveau456"))

    def test_post_mots_de_passe_differents_ne_change_pas(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {
            "password": "nouveau456",
            "password2": "different789",
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ancien123"))

    def test_post_mot_de_passe_trop_court_ne_change_pas(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {
            "password": "ab",
            "password2": "ab",
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ancien123"))

    def test_post_mot_de_passe_vide_ne_change_pas(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {
            "password": "",
            "password2": "",
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ancien123"))


# ─────────────────────────────────────────────
# UserListView / UserCreateView / UserDeleteView
# ─────────────────────────────────────────────

class UserManagementAccessTest(TestCase):
    """Les vues de gestion utilisateurs sont reservees aux superadmins."""

    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser()
        self.regular_user = make_user(username="agent")

    def test_user_list_interdit_sans_superadmin(self):
        self.client.force_login(self.regular_user)
        resp = self.client.get(reverse("frontend:users"))
        self.assertIn(resp.status_code, [302, 403])

    def test_user_list_accessible_superadmin(self):
        self.client.force_login(self.superuser)
        resp = self.client.get(reverse("frontend:users"))
        self.assertEqual(resp.status_code, 200)

    def test_user_create_accessible_superadmin(self):
        self.client.force_login(self.superuser)
        resp = self.client.get(reverse("frontend:user_create"))
        self.assertEqual(resp.status_code, 200)

    def test_user_delete_interdit_sans_superadmin(self):
        target = make_user(username="cible")
        self.client.force_login(self.regular_user)
        resp = self.client.post(
            reverse("frontend:user_delete", kwargs={"pk": target.pk})
        )
        self.assertIn(resp.status_code, [302, 403])
        self.assertTrue(User.objects.filter(pk=target.pk).exists())
