from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.test import TestCase, override_settings
from posts.models import Post, Group, Comment, Follow
from django.urls import reverse
from django.core.cache import cache
import tempfile

from PIL import Image

TEST_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
User = get_user_model()


@override_settings(CACHES=TEST_CACHE)
class TestPostsUnauthorized(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test',
                                             email='bk@gmail.com',
                                             password=12345)

    def test_no_auth_user_redirect(self):
        resp = self.client.post(
            reverse('new_post'),
            data={'group': '', 'text': 'test12345'}
        )
        self.assertRedirects(resp, "/auth/login/?next=/new/")
        self.assertEqual(Post.objects.all().count(), 0)

    def test_comment(self):
        post = Post.objects.create(text='abcdefg', author=self.user)
        response = self.client.get(reverse('add_comment', args=['mike', '1']))
        self.assertRedirects(response,
                             f'/auth/login/?next=/'
                             f'{self.user.username}/'
                             f'{post.pk}/comment',
                             status_code=302,
                             target_status_code=200)
        comment = Comment.objects.filter(text='pula').count()
        self.assertNotEqual(comment, 0)


class TestPostsAuthorized(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="Testuser",
            email="test@gmail.com",
            password="Raieqweqwe2seromwe!",
        )
        self.group = Group.objects.create(
            title="title",
            slug='slug-qwerewq',
            description='description',
        )
        self.client.force_login(self.user)

    def test_profile(self):
        response = self.client.get(
            reverse('profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(CACHES=TEST_CACHE)
    def test_post(self):
        resp = self.client.post(
            reverse("new_post"),
            data={'group': self.group.id, 'text': 'test'},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)
        created_post = Post.objects.first()
        self.assertEqual(created_post.text, 'test')
        self.assertEqual(created_post.group, self.group)
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(Post.objects.count(), 1)

    def check_contain_post(self, url, user, group, text):
        resp = self.client.get(url)
        if 'paginator' in resp.context.keys():
            post = resp.context['page'][0]
        else:
            post = resp.context['post']
        self.assertEqual(post.text, text)
        self.assertEqual(post.group, group)
        self.assertEqual(post.author, self.user)

    @override_settings(CACHES=TEST_CACHE)
    def test_new_post(self):
        post = Post.objects.create(text='text',
                                   author=self.user,
                                   group=self.group)
        list_urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post',
                    kwargs={'username': self.user.username,
                            'post_id': post.id}),
        ]
        for url in list_urls:
            with self.subTest(url=url):
                self.check_contain_post(url, self.user, self.group, post.text)

    @override_settings(CACHES=TEST_CACHE)
    def test_edit_post(self):
        post = Post.objects.create(text='text_test',
                                   author=self.user,
                                   group=self.group)
        list_urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post', kwargs={'username': self.user.username,
                                    'post_id': post.id}),
        ]
        new_group = Group.objects.create(
            title="new_title",
            slug='slug-new',
            description='new_description',
        )
        post_data = {
            'group': new_group.id,
            'text': 'text_ediq  weter',
        }
        edit_url = reverse('post_edit', kwargs={
            'username': self.user.username,
            'post_id': post.id,
        }
                           )
        self.client.post(edit_url, data=post_data)

        for url in list_urls:
            with self.subTest(url=url):
                self.check_contain_post(url,
                                        self.user,
                                        new_group,
                                        post_data['text'])


class TestCache(TestCase):
    def setUp(self):
        self.first_client = Client()
        self.second_client = Client()
        self.user = User.objects.create_user(username='TestUser',
                                             password='ASKnfbg123_2')
        self.first_client.force_login(self.user)

    def test_cache(self):
        self.second_client.get(reverse('index'))
        self.first_client.post(reverse('new-post'), {'text': 'Test text'})
        response = self.second_client.get(reverse('index'))
        self.assertNotContains(response, 'Test text')


class TestFollowSystem(TestCase):
    def setUp(self):
        self.client = Client()
        self.following = User.objects.create_user(
            username='TestFollowing', password='password')
        self.follower = User.objects.create_user(username='TestFollower',
                                                 password='password')
        self.user = User.objects.create_user(username='user',
                                             password='password')
        self.post = Post.objects.create(author=self.following,
                                        text='FollowTest')
        self.client.force_login(self.follower)
        self.link = Follow.objects.filter(user=self.follower,
                                          author=self.following)

    def test_follow(self):
        response = self.client.get(reverse('profile_follow', kwargs={
            'username': self.following}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.link.exists())
        self.assertEqual(1, Follow.objects.count())

    def test_unfollow(self):
        response = self.client.get(
            reverse('profile_unfollow',
                    kwargs={'username': self.following}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.link.exists())
        self.assertEqual(0, Follow.objects.count())

    def test_follow_index(self):
        Follow.objects.create(user=self.follower, author=self.following)
        follow_index_url = reverse('follow_index')
        response = self.client.get(follow_index_url)
        self.assertContains(response, self.post.text)

        self.client.force_login(self.user)
        response = self.client.get(follow_index_url)
        self.assertNotContains(response, self.post.text)


class TestComments(TestCase):
    def setUp(self):
        self.logged_client = Client()
        self.client = Client()
        self.user = User.objects.create_user(username='user',
                                             password='password')
        self.post = Post.objects.create(author=self.user,
                                        text='TestText')
        self.logged_client.force_login(self.user)

    def test_comment(self):
        comment_url = reverse('add_comment',
                              kwargs={'username': self.user,
                                      'post_id': self.post.id})
        self.logged_client.post(comment_url, {'text': 'Test Comment'},
                                follow=True)

        comment = Comment.objects.filter(text='Test Comment').exists()
        response = self.logged_client.get(comment_url, follow=True)
        self.assertContains(response, 'Test Comment')
        self.assertTrue(comment)

        self.client.post(comment_url, {'text': 'Unlogged Comment'},
                         follow=True)
        self.assertEqual(0, Comment.objects.filter(
            text='Unlogged Comment').count())


class ImageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username="tester", email="Test@mail.com", password="12345"
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            title="ping-echo",
            slug="ping-group",
            description="Ping-ping-ping"
        )
        self.post = Post.objects.create(text='hi', group=self.group,
                                        author=self.user)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img:
            image = Image.new('RGB', (200, 200), 'white')
            image.save(img, 'PNG')
        self.image = open(img.name, mode='rb')

        with tempfile.NamedTemporaryFile(suffix='.doc',
                                         delete=False) as not_img:
            not_img.write(b'test')
        self.not_image = open(not_img.name, 'rb')

    def test_image(self):
        with self.image as img:
            self.client.post(reverse('post_edit',
                                     kwargs={'username': self.user,
                                             'post_id': self.post.id}),
                             {'group': self.group.id,
                              'text': 'post with image',
                              'image': img}, redirect=True)

        tag = '<img class='
        response_profile = self.client.get(reverse(
            "/tester/", kwargs={'username': self.user.username}))
        self.assertContains(response_profile, tag)
        response_index = self.client.get(reverse("/"))
        self.assertContains(response_index, tag)
        response_group = self.client.get(reverse(
            "/group/ping-group/", kwargs={'slug': self.group.slug}))
        self.assertContains(response_group, tag)

    def test_image_upload(self):
        with self.not_image as img:
            wrong_img = self.client.post(reverse('post_edit',
                                                 kwargs={'username': self.user,
                                                         'post_id':
                                                             self.post.id}),
                                         {'group': self.group.id,
                                          'text': 'post with image',
                                          'image': img}, redirect=True)

        error = ('Загрузите правильное изображение. Файл, который вы '
                 'загрузили, поврежден или не является изображением.')
        self.assertFormError(wrong_img, 'form', 'image', error)