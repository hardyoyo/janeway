__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from dateutil import parser as dateparser
from mock import Mock
import os

from django.http import Http404
from django.test import TestCase
from django.utils import translation
from django.conf import settings

from core.models import Account
from identifiers import logic as id_logic
from journal import models as journal_models
from submission import (
    decorators,
    forms,
    logic,
    models,
)

from utils.install import update_xsl_files, update_settings, update_issue_types


# Create your tests here.
class SubmissionTests(TestCase):
    roles_path = os.path.join(
        settings.BASE_DIR,
        'utils',
        'install',
        'roles.json'
    )
    fixtures = [roles_path]

    def test_new_journals_has_submission_configuration(self):
        if not self.journal_one.submissionconfiguration:
            self.fail('Journal does not have a submissionconfiguration object.')

    @staticmethod
    def create_journal():
        """
        Creates a dummy journal for testing
        :return: a journal
        """
        update_xsl_files()
        update_settings()
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.title = "Test Journal: A journal of tests"
        journal_one.save()
        update_issue_types(journal_one)

        return journal_one

    @staticmethod
    def create_authors():
        author_1_data = {
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }
        author_2_data = {
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Sr.',
            'first_name': 'Mauro',
            'last_name': 'Sanchez',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }
        author_1 = Account.objects.create(email="1@t.t", **author_1_data)
        author_2 = Account.objects.create(email="2@t.t", **author_1_data)

        return author_1, author_2

    def setUp(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one = self.create_journal()

    def test_article_how_to_cite(self):
        issue = journal_models.Issue.objects.create(journal=self.journal_one)
        journal_models.Issue
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
            primary_issue=issue,
            date_published=dateparser.parse("2020-01-01"),
            page_numbers = "2-4"
        )
        author = models.FrozenAuthor.objects.create(
            article=article,
            first_name="Mauro",
            middle_name="Middle",
            last_name="Sanchez",
        )
        id_logic.generate_crossref_doi_with_pattern(article)

        expected = """
        <p>
         Sanchez, M. M.,
        (2020) “Test article: a test article”,
        <i>Janeway JS</i> 1(1), p.2-4.
        doi: <a href="https://doi.org/{0}">https://doi.org/{0}</a></p>
        """.format(article.get_doi())
        self.assertHTMLEqual(expected, article.how_to_cite)

    def test_article_how_to_cite(self):
        issue = journal_models.Issue.objects.create(
                journal=self.journal_one,
                issue="0",
                volume=1,
        )
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
            primary_issue=issue,
            date_published=dateparser.parse("2020-01-01"),
            page_numbers = "2-4"
        )
        author = models.FrozenAuthor.objects.create(
            article=article,
            first_name="Mauro",
            middle_name="Middle",
            last_name="Sanchez",
        )
        id_logic.generate_crossref_doi_with_pattern(article)

        expected = """
        <p>
         Sanchez, M. M.,
        (2020) “Test article: a test article”,
        <i>Janeway JS</i> 1, p.2-4.
        doi: <a href="https://doi.org/{0}">https://doi.org/{0}</a></p>
        """.format(article.get_doi())
        self.assertHTMLEqual(expected, article.how_to_cite)

    def test_custom_article_how_to_cite(self):
        issue = journal_models.Issue.objects.create(journal=self.journal_one)
        journal_models.Issue
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
            primary_issue=issue,
            date_published=dateparser.parse("2020-01-01"),
            page_numbers = "2-4",
            custom_how_to_cite = "Banana",
        )
        author = models.FrozenAuthor.objects.create(
            article=article,
            first_name="Mauro",
            middle_name="M",
            last_name="Sanchez",
        )
        id_logic.generate_crossref_doi_with_pattern(article)

        expected = "Banana"
        self.assertHTMLEqual(expected, article.how_to_cite)

    def test_funding_is_enabled_decorator_enabled(self):
        request = Mock()
        journal = self.journal_one
        journal.submissionconfiguration.funding = True
        request.journal = journal
        func = Mock()
        decorated = decorators.funding_is_enabled(func)
        decorated(request)
        self.assertTrue(func.called,
            "Funding pages not available when they should be")


    def test_funding_is_enabled_decorator_disabled(self):
        request = Mock()
        journal = self.journal_one
        journal.submissionconfiguration.funding = False
        request.journal = journal
        func = Mock()
        decorated = decorators.funding_is_enabled(func)
        with self.assertRaises(
            Http404, msg="Funding pages available when they shouldn't"
        ):
            decorated(request)

    def test_snapshot_author_metadata_correctly(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()[0]
        keys = {'first_name', 'last_name', 'department', 'institution'}

        self.assertDictEqual(
            {k: getattr(author, k) for k in keys},
            {k: getattr(frozen, k) for k in keys},
        )

    def test_snapshot_author_order_correctly(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author_1, author_2 = self.create_authors()
        logic.add_user_as_author(author_1, article)
        logic.add_user_as_author(author_2, article)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()
        self.assertListEqual(
            [author_1, author_2],
            [f.author for f in article.frozen_authors().order_by("order")],
            msg="Authors frozen in the wrong order",
        )

    def test_snapshot_author_metadata_do_not_override(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()[0]
        new_department = "New department"
        frozen.department = new_department
        frozen.save()
        article.snapshot_authors(force_update=False)

        self.assertEqual(
            frozen.department, new_department,
            msg="Frozen author edits have been overriden by snapshot_authors",
        )

    def test_snapshot_author_metadata_override(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)

        article.snapshot_authors()
        new_department = "New department"
        article.frozen_authors().update(department=new_department)
        article.snapshot_authors(force_update=True)
        frozen = article.frozen_authors().all()[0]

        self.assertEqual(
            frozen.department, author.department,
            msg="Frozen author edits have been overriden by snapshot_authors",
        )

    def test_frozen_author_prefix(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)
        article.snapshot_authors()

        prefix = "Lord"
        article.frozen_authors().update(name_prefix=prefix)
        frozen = article.frozen_authors().all()[0]

        self.assertTrue(frozen.full_name().startswith(prefix))

    def test_frozen_author_prefix(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)
        article.snapshot_authors()

        suffix = "Jr"
        article.frozen_authors().update(name_suffix=suffix)
        frozen = article.frozen_authors().all()[0]

        self.assertTrue(frozen.full_name().endswith(suffix))

    def test_snapshot_author_order_author_added_later(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author_1, author_2 = self.create_authors()
        logic.add_user_as_author(author_1, article)
        logic.add_user_as_author(author_2, article)
        no_order_author = Account.objects.create(
            email="no_order@t.t",
            first_name="no order",
            last_name="no order",
        )
        article.authors.add(no_order_author)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()
        self.assertListEqual(
            [author_1, author_2, no_order_author],
            [f.author for f in article.frozen_authors().order_by("order")],
            msg="Authors frozen in the wrong order",
        )

    def test_article_keyword_default_order(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            models.KeywordArticle.objects.get_or_create(
                keyword=kw_obj,
                article=article
            )

        self.assertEqual(
            keywords,
            [kw.word for kw in article.keywords.all()],
        )

    def test_article_keyword_add(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            article.keywords.add(kw_obj)

        self.assertEqual(
            keywords,
            [kw.word for kw in article.keywords.all()],
        )

    def test_article_keyword_remove(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        kw_objs = []
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            kw_objs.append(kw_obj)
            article.keywords.add(kw_obj)

        article.keywords.remove(kw_objs[1])
        keywords.pop(1)

        self.assertEqual(
            keywords,
            [kw.word for kw in article.keywords.all()],
        )

    def test_article_keyword_clear(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            article.keywords.add(kw_obj)
        article.keywords.clear()

        self.assertEqual(
            [],
            [kw.word for kw in article.keywords.all()],
        )

    def test_edit_section(self):
        """ Ensures editors can select sections that are not submissible"""
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test of sections",
        )
        with translation.override("en"):
            section = models.Section.objects.create(
                journal=self.journal_one,
                name="section",
                public_submissions=False,
            )
            form = forms.ArticleInfo(instance=article)
            self.assertTrue(section in form.fields["section"].queryset)

    def test_select_disabled_section_submit(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test of sections",
        )
        with translation.override("en"):
            section = models.Section.objects.create(
                journal=self.journal_one,
                name="section",
                public_submissions=False,
            )
            form = forms.ArticleInfoSubmit(instance=article)
            self.assertTrue(section not in form.fields["section"].queryset)

    def test_article_issue_title(self):
        from utils.testing import helpers
        issue = helpers.create_issue(
            self.journal_one,
            vol=5,
            number=4,
        )

        date_time_str = '2025-11-01 12:00:00'
        date_time = dateparser.parse(date_time_str)
        from django.utils.timezone import make_aware
        issue.date = make_aware(date_time)
        issue.issue_title = 'Fall 2025'
        issue.save()

        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: A test of page numbers",
            first_page=3,
            last_page=5,
            primary_issue=issue,
        )

        expected_article_issue_title = 'Volume 5 &bull; Issue 4 &bull; ' \
                                       '2025 &bull; Fall 2025 &bull; 3&ndash;5'
        self.assertEqual(expected_article_issue_title, article.issue_title)

        article.page_numbers='x–ix'
        expected_article_issue_title = 'Volume 5 &bull; Issue 4 &bull; ' \
                                       '2025 &bull; Fall 2025 &bull; x–ix'
        self.assertEqual(expected_article_issue_title, article.issue_title)

        article.first_page = None
        article.last_page = None
        article.page_numbers = None
        article.total_pages = 1
        expected_article_issue_title = 'Volume 5 &bull; Issue 4 &bull; ' \
                                       '2025 &bull; Fall 2025 &bull; 1 page'
        self.assertEqual(expected_article_issue_title, article.issue_title)


class FrozenAuthorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.frozen_author = models.FrozenAuthor.objects.create(
            name_prefix='Dr.',
            first_name='S.',
            middle_name='Bella',
            last_name='Rogers',
            name_suffix='Esq.',
        )

    def test_full_name(self):
        self.assertEqual('Dr. S. Bella Rogers Esq.', self.frozen_author.full_name())
