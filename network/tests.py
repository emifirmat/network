from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Max
from django.test import Client, TestCase
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver

from .models import User, Post, Follow, Like

class CommonSetUp:
    """Create Post instances for testing"""
    def setUp(self):
         # Create users
        self.user1 = User.objects.create_user(username="emi", email="emi@cai.com", 
            password="1234")
        self.user2 = User.objects.create_user(username="abi", email="abi@cai.com", 
            password="1234")
        self.user3 = User.objects.create_user(username="carlos", email="carlos@cai.com", 
            password="1234")
        
        # Create posts
        self.p1 = Post.objects.create(content="abc", creator=self.user1)
        self.p2 = Post.objects.create(content="def", creator=self.user2)
        self.p3 = Post.objects.create(content="ghi", creator=self.user1)

        # Create likes
        l1 = Like.objects.create(user=self.user1, post=self.p1)
        l2 = Like.objects.create(user=self.user2, post=self.p1)
        l3 = Like.objects.create(user=self.user2, post=self.p3)

        # Create follow
        f1 = Follow.objects.create(user_following=self.user2,
            user_followed=self.user3)
        f2 = Follow.objects.create(user_following=self.user2,
            user_followed=self.user1)
        

class NetworkBackTestCase(CommonSetUp, TestCase):
    """Tests Network app from back"""
    # Test Models
    def test_post_count(self):
        posts = Post.objects.filter(creator=1)
        self.assertEqual(posts.count(), 2)

        posts = Post.objects.filter(creator=2) 
        self.assertEqual(posts.count(), 1)

    def test_post_max_id(self):
        max_post_id = Post.objects.all().aggregate(Max("id"))["id__max"]
        self.assertEqual(max_post_id, 3)

    def test_post_likes(self):
        likes = Like.objects.filter(post=1)
        likes2 = Like.objects.filter(post=2)
        likes3 = Like.objects.filter(post=3)
        
        self.assertEqual(likes.count(), 2)
        self.assertEqual(likes2.count(), 0)
        self.assertEqual(likes3.count(), 1)

    def test_post_likes_duplication(self):
        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.user1, post=self.p1)

    def test_follow(self):
        following = Follow.objects.filter(user_following=2)
        followed = Follow.objects.all().values_list("user_followed", flat=True)

        self.assertEqual(following.count(), 2)
        self.assertEqual(followed.count(), 2)
        self.assertIn(1, followed)
        self.assertIn(3, followed)

    def test_follow_duplication(self):
        with self.assertRaises(IntegrityError):
            Follow.objects.create(user_following=self.user2,
                user_followed=self.user1)
    
    def test_follow_ValidationError(self):
        with self.assertRaises(ValidationError):
            f3 = Follow.objects.create(user_following=self.user1,
                user_followed=self.user1)
            f3.follow_is_valid()

    # Test Web Pages
    def test_index_page(self):
        c = Client()
        # Not logged
        response = c.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 3)
        self.assertIsNone(response.context['liked_posts'])
        
        # Logged
        c.force_login(self.user1)
        response = c.get("/")
        self.assertEqual(len(response.context['posts']), 3)
        self.assertEqual(len(response.context['liked_posts']), 1)

    def test_post_submission(self):
        c = Client()
        c.force_login(self.user2)
        form = {
            'content': 'testing',
        }
        response = c.post(reverse("network:index"), form)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.get(creator=self.user2, content='testing'))
        # Test new post exists
        response = c.get(reverse("network:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 4)

    def test_following_page(self):
        c = Client()
        # Not logged
        response = c.get(reverse("network:following"))
        self.assertEqual(response.status_code, 302)

        # Logged user2
        c.force_login(self.user2)
        response = c.get(reverse("network:following"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 2)
        self.assertEqual(len(response.context['liked_posts']), 2)

        # Logged user3
        c.force_login(self.user3)
        response = c.get(reverse("network:following"))
        self.assertEqual(len(response.context['posts']), 0)
        self.assertEqual(len(response.context['liked_posts']), 0)

    def test_profile_page(self):
        c = Client()
        # Not logged
        response = c.get('/profile/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 1)
        self.assertIsNone(response.context['liked_posts'])
        self.assertEqual(response.context['profile_user'], self.user2)
        
        # Logged user 3
        c.force_login(self.user3)
        response = c.get('/profile/2')
        self.assertFalse(response.context['profile_user'].is_following)


class NetworkFrontTestCase(CommonSetUp, StaticLiveServerTestCase):
    """Tests Network app from back"""
    @classmethod
    def setUpClass(cls):
        """Set up selenium server """
        super().setUpClass()
        cls.driver = WebDriver()
        cls.driver.implicitly_wait(10)
        
    @classmethod
    def tearDownClass(cls):
        """Close selenium server"""
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Add login setUp"""
        super().setUp()
        self.driver.get(f"{self.live_server_url}/login")
        
        # Input username and password
        username = self.driver.find_element(By.NAME, 'username')
        username.send_keys("emi")
        password = self.driver.find_element(By.NAME, 'password')
        password.send_keys("1234")

        # Press submit
        self.driver.find_element(By.XPATH, "//input[@type='submit']").click()
        self.driver.implicitly_wait(10)

    # Test front with Selenium
    def test_login(self):
        self.assertTrue(self.driver.find_element(By.ID, "username"), "emi")

    def test_index_edit_post(self):
        # Original content
        content = self.driver.find_element(By.ID, "content-3")
        self.assertEqual(content.text, "ghi")

        # Click Edit on last post
        edit_button = self.driver.find_elements(By.CLASS_NAME, "editPost")
        edit_button[0].click()
        
        # Check there's only 2 edit buttons
        self.assertTrue(len(edit_button), 2)

        # Add and send new content
        form_div = self.driver.find_element(By.ID, "form-3")
        text_area = form_div.find_element(By.XPATH, ".//textarea")
        text_area.clear()
        text_area.send_keys("jkl")
        form_div.find_element(By.XPATH, ".//input[@type='submit']").click()
        
        # I have to find the element again
        content = self.driver.find_element(By.ID, "content-3")
        self.assertEqual(content.text, "jkl")

        # Re-edit same post
        self.driver.find_elements(By.CLASS_NAME, "editPost")[0].click()
        form_div = self.driver.find_element(By.ID, "form-3")
        text_area = form_div.find_element(By.XPATH, ".//textarea")
        text_area.clear()
        text_area.send_keys("mni")
        form_div.find_element(By.XPATH, ".//input[@type='submit']").click()
        self.driver.implicitly_wait(10)
        content = self.driver.find_element(By.ID, "content-3")
        self.assertEqual(content.text, "mni")

    def test_index_like_button(self):
        likes = self.driver.find_elements(By.CLASS_NAME, "like-container")
        original_count = ["❤️1", "❤️0", "❤️2"]
        new_count = ["❤️2", "❤️1", "❤️1"]
        original_like_tag = ["Like", "Like", "Unlike"]
        new_like_tag = ["Unlike", "Unlike", "Like"]

        # Like all the posts
        for i in range(len(likes)):
            # Test original likes
            like_img = likes[i].find_element(By.XPATH, './/img')
            like_count = likes[i].find_elements(By.XPATH, './/span')[0] 
            like_text = likes[i].find_elements(By.XPATH, './/span')[1]

            # P3=1 like by U2, P2= 0 like, P1= 2 likes by U1,U2
            self.assertEqual(like_text.text, original_like_tag[i])
            self.assertEqual(like_count.text, original_count[i])
            
            # Like the post and test again
            like_img.click()
            like_count = likes[i].find_elements(By.XPATH, './/span')[0]
            self.assertEqual(like_text.text, new_like_tag[i])
            self.assertEqual(like_count.text, new_count[i])

    def test_index_paginator_next(self):
        # Create posts in order to use paginator
        for i in range(15):
            Post.objects.create(content=f"{i}", creator=self.user1)
        self.driver.implicitly_wait(5)
        self.driver.refresh()

        # Next page
        self.driver.find_element(By.ID, "next").click()
        self.driver.implicitly_wait(5)
        post = self.driver.find_elements(By.CLASS_NAME, "card-body")[0]
        post = post.find_element(By.XPATH, ".//p")
        self.assertTrue(post.text, "14")
        
        # Previous page
        self.driver.find_element(By.ID,"previous").click()
        self.driver.implicitly_wait(5)
        post = self.driver.find_elements(By.CLASS_NAME, "card-body")[0]
        post = post.find_element(By.XPATH, ".//p")
        self.assertTrue(post.text, "abc")

        # Last page
        self.driver.find_element(By.ID,"last").click()
        self.driver.implicitly_wait(5)
        post = self.driver.find_elements(By.CLASS_NAME, "card-body")[2]
        post = post.find_element(By.XPATH, ".//p")
        self.assertTrue(post, "13")
        
        # First page
        self.driver.find_element(By.ID,"first").click()
        self.driver.implicitly_wait(5)
        post = self.driver.find_elements(By.CLASS_NAME, "card-body")[2]
        post = post.find_element(By.XPATH, ".//p")
        self.assertTrue(post.text, "def")

    def test_profile_follow_unfollow(self):
        # Go to abi's profile 
        path = self.driver.find_elements(By.CLASS_NAME, "card-header")
        path[1].find_element(By.XPATH, ".//a").click()
        self.assertEqual(self.driver.title, "Profile")

        # Original following(2) followers(0)
        button_follow = self.driver.find_element(By.ID, "follow")
        followers = self.driver.find_element(By.ID, "followersCount")
        following = self.driver.find_element(By.ID, "followingCount")
        
        self.assertEqual(button_follow.text, "Follow")
        self.assertEqual(followers.text, "0")
        self.assertEqual(following.text, "2")

        # Follow and check follow numbers
        button_follow.click()
        self.driver.implicitly_wait(5)

        # Unfollow and check follow numbers    
        self.assertEqual(button_follow.text, "Unfollow")
        self.assertEqual(followers.text, "1")

        # Check own profile
        self.driver.find_element(By.ID, "nav-3").click()
        followers = self.driver.find_element(By.ID, "followersCount")
        following = self.driver.find_element(By.ID, "followingCount")
        self.assertEqual(followers.text, "1")
        self.assertEqual(following.text, "1")