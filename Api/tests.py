import json

from django.test import TestCase

from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token

from .models import User, Idea, FollowRequest

# Create your tests here.

class UserQueryTest(GraphQLTestCase):

    GRAPHQL_URL = 'http://localhost:8000/graphql/'

    def setUp(self):
        User.objects.create(email="test1@test1.com", username="usertest1")
        User.objects.create(email="test2@test2.com", username="usertest2")

    def test_resolve_users(self):
        response = self.query(
            '''
            query {
                users {
                    username
                    email
                }
            }
            '''
        )
        compare = {"data":{"users":[{"username":"usertest1","email":"test1@test1.com"},{"username":"usertest2","email":"test2@test2.com"}]}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)
    
    def test_resolve_me(self):
        user = User.objects.get(email="test1@test1.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            query {
                me {
                    username
                    email
                    ideaUser{
                        content
                    }
                    followers{
                        username
                    }
                    following{
                        username
                    }
                }
            }
            ''',
            headers=header
        )
        compare = {"data": {"me":{"username":"usertest1","email":"test1@test1.com","ideaUser":[],"followers":[],"following":[]}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)

    def test_resolve_search_users(self):
        user = User.objects.get(email="test1@test1.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            query searchUsers($username: String!){
                searchUsers(username: $username){
                    username
                    email
                }
            }
            ''',
            headers=header,
            variables={'username':'test'}
        )
        compare = {"data": {"searchUsers":[{"username":"usertest2","email":"test2@test2.com"}]}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)

    def test_resolve_forgotten_password(self):
        response = self.query(
            '''
            query forgottenPassword($email: String!){
                forgottenPassword(email: $email)
            }
            ''',
            variables={'email': 'test1@test1.com'}
        )

        compare = {"data": {"forgottenPassword": "Email sent to test1@test1.com"}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)


class UserMutationTest(GraphQLTestCase):

    GRAPHQL_URL = 'http://localhost:8000/graphql/'

    def setUp(self):
        user1 = User.objects.create(email="test1@test1.com", username="usertest1")
        user2 = User.objects.create(email="test2@test2.com", username="usertest2")
        user2.following.add(user1)

    def test_register_mutation(self):
        response = self.query(
            '''
            mutation register($username: String!, $email: String!, $password: String!){
                register(username: $username, email: $email, password: $password){
                    success
                    error
                    user{
                        username
                        email
                    }
                }
            }
            ''',
            variables={'email':'test3@test3.com', 'username': 'usertest3', 'password': 'usertest1234'}
        )
        compare = {"data":{"register":{"success": True, "error": None,"user":{"username":"usertest3","email":"test3@test3.com"}}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)
    
    def test_change_password_mutation(self):
        user = User.objects.get(email="test1@test1.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation changePassword($password: String!){
                changePassword(password: $password){
                    success
                    error
                }
            }
            ''',
            headers = header,
            variables = {'password': 'usertest123456'}
        )
        compare = {"data":{"changePassword":{"success":True,"error":None}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)
    
    def test_delete_follow_mutation(self):
        user = User.objects.get(email="test2@test2.com")
        user_unfollow = User.objects.get(email="test1@test1.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation unfollow($idUser: ID!){
                unfollow(idUser: $idUser){
                    success
                    error
                    message
                }
            }
            ''',
            headers=header,
            variables={'idUser': user_unfollow.id}
        )
        compare = {"data":{"unfollow":{"success":True,"error":None,"message":f"Unfollow {user_unfollow.username}"}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)
    
    def test_delete_follower_mutation(self):
        user = User.objects.get(email="test1@test1.com")
        follower = User.objects.get(email="test2@test2.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation removeFollower($idUser: ID!){
                removeFollower(idUser: $idUser){
                    success
                    error
                    message
                }
            }
            ''',
            headers=header,
            variables={'idUser': follower.id}
        )
        compare = {"data": {"removeFollower": {"success": True, "error": None, "message": f'{follower.username} removed from follower list'}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)


class IdeaQueryTest(GraphQLTestCase):

    GRAPHQL_URL = 'http://localhost:8000/graphql/'

    def setUp(self):
        user1 = User.objects.create(email="test1@test1.com", username="usertest1")
        user2 = User.objects.create(email="test2@test2.com", username="usertest2")
        user3 = User.objects.create(email="test3@test3.com", username="usertest3")
        user2.following.add(user1)
        Idea.objects.create(content="primera idea de usertest1", pub_user=user1, visibility=Idea.PUBLIC)
        Idea.objects.create(content="segunda idea de usertest1", pub_user=user1, visibility=Idea.PROTECTED)
        Idea.objects.create(content="tercera idea de usertest1", pub_user=user1, visibility=Idea.PRIVATE)
        Idea.objects.create(content="primera idea de usertest2", pub_user=user2, visibility=Idea.PUBLIC)
        Idea.objects.create(content="segunda idea de usertest2", pub_user=user2, visibility=Idea.PROTECTED)
        Idea.objects.create(content="tercera idea de usertest2", pub_user=user2, visibility=Idea.PRIVATE)
        Idea.objects.create(content="primera idea de usertest3", pub_user=user3, visibility=Idea.PUBLIC)
        Idea.objects.create(content="segunda idea de usertest3", pub_user=user3, visibility=Idea.PROTECTED)
        Idea.objects.create(content="tercera idea de usertest3", pub_user=user3, visibility=Idea.PRIVATE)

    def test_resolve_list_all_ideas(self):
        user = User.objects.get(email="test2@test2.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            query {
                listAllIdeas{
                    content
                    visibility
                    pubUser{
                        username
                    }
                }
            }
            ''',
            headers=header
        )
        compare = {"data":{
            "listAllIdeas":[
                {"content":"primera idea de usertest3","visibility":"PUBLIC","pubUser":{"username":"usertest3"}},
                {"content":"tercera idea de usertest2","visibility":"PRIVATE","pubUser":{"username":"usertest2"}},
                {"content":"segunda idea de usertest2","visibility":"PROTECTED","pubUser":{"username":"usertest2"}},
                {"content":"primera idea de usertest2","visibility":"PUBLIC","pubUser":{"username":"usertest2"}},
                {"content":"segunda idea de usertest1","visibility":"PROTECTED","pubUser":{"username":"usertest1"}},
                {"content":"primera idea de usertest1","visibility":"PUBLIC","pubUser":{"username":"usertest1"}}]}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)

    def test_resolve_list_my_ideas(self):
        user = User.objects.get(email="test2@test2.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            query{
                listMyIdeas{
                    content
                    visibility
                    pubUser{
                        username
                    }
                }
            }
            ''',
            headers=header
        )
        compare = {"data":{
            "listMyIdeas":[
                {"content":"tercera idea de usertest2","visibility":"PRIVATE","pubUser":{"username":"usertest2"}},
                {"content":"segunda idea de usertest2","visibility":"PROTECTED","pubUser":{"username":"usertest2"}},
                {"content":"primera idea de usertest2","visibility":"PUBLIC","pubUser":{"username":"usertest2"}}]}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)
    
    def test_resolve_list_followed_ideas(self):
        user = User.objects.get(email="test2@test2.com")
        user_followed = User.objects.get(email="test1@test1.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            query listFollowedIdeas($idUser: ID!){
                listFollowedIdeas(idUser: $idUser){
                    content
                    visibility
                    pubUser{
                        username
                    }
                }
            }
            ''',
            headers=header,
            variables={'idUser': user_followed.id}
        )
        compare = {"data":{
            "listFollowedIdeas":[
                {"content":"segunda idea de usertest1","visibility":"PROTECTED","pubUser":{"username":"usertest1"}},
                {"content":"primera idea de usertest1","visibility":"PUBLIC","pubUser":{"username":"usertest1"}}]}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)


class IdeaMutationTest(GraphQLTestCase):
    
    GRAPHQL_URL = 'http://localhost:8000/graphql/'

    def setUp(self):
        user1 = User.objects.create(email="test1@test1.com", username="usertest1")
        user2 = User.objects.create(email="test2@test2.com", username="usertest2")
        Idea.objects.create(content="first idea of usertest2", pub_user=user2, visibility=Idea.PUBLIC)
    
    def test_add_idea_mutation(self): 
        user = User.objects.get(email="test1@test1.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation addIdea($content: String!, $visibility: String){
                addIdea(content: $content, visibility: $visibility){
                    success
                    error
                    idea{
                        content
                        visibility
                        pubUser{
                            username
                        }
                    }
                }
            }
            ''',
            headers=header,
            variables={'content':'test idea content'}
        )
        compare = {"data":{"addIdea":{"success":True, "error":None, "idea":{"content":"test idea content","visibility":"PUBLIC","pubUser":{"username":"usertest1"}}}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)

    def test_edit_idea_mutation(self):
        user = User.objects.get(email="test2@test2.com")
        idea_user = user.idea_user.first()
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation editIdea($id: ID!, $content: String, $visibility: String){
                editIdea(id: $id, content: $content, visibility: $visibility){
                    success
                    error
                    idea{
                        content
                        visibility
                    }
                }
            }
            ''',
            headers=header,
            variables={'id': idea_user.id, 'content': 'test idea modified', 'visibility':'private'}
        )
        compare = {"data":{"editIdea":{"success":True,"error":None,"idea":{"content":"test idea modified","visibility":"PRIVATE"}}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)

    def test_delete_idea(self):
        user = User.objects.get(email="test2@test2.com")
        idea_user = user.idea_user.first()
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation deleteIdea($id: ID!){
                deleteIdea(id: $id){
                    success
                    error
                    message
                }
            }
            ''',
            headers=header,
            variables={'id': idea_user.id }
        )
        compare = {"data":{"deleteIdea":{"success":True,"error":None,"message":"Delete success"}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)
        

class FollowRequestQueryTest(GraphQLTestCase):

    GRAPHQL_URL = 'http://localhost:8000/graphql/'

    def setUp(self):
        user1 = User.objects.create(email="test1@test1.com", username="usertest1")
        user2 = User.objects.create(email="test2@test2.com", username="usertest2")
        FollowRequest.objects.create(requester=user2, to_follow=user1)
    
    def test_resolve_follow_up_request(self):
        user = User.objects.get(email="test1@test1.com")
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            query{
                followUpRequest{
                    requester{
                        username
                    }
                    status
                }
            }
            ''',
            headers=header
        )
        compare = {"data":{"followUpRequest":[{"requester":{"username": "usertest2"},"status":"PENDING"}]}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)


class FollowRequestMutationTest(GraphQLTestCase):

    GRAPHQL_URL = 'http://localhost:8000/graphql/'

    def setUp(self):
        user1 = User.objects.create(email="test1@test1.com", username="usertest1")
        user2 = User.objects.create(email="test2@test2.com", username="usertest2")
        FollowRequest.objects.create(requester=user2, to_follow=user1)
    
    def test_send_follow_request(self):
        user_req = User.objects.get(email="test1@test1.com")
        user_foll = User.objects.get(email="test2@test2.com")
        token = get_token(user_req)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation sendFollowRequest($idUser: ID!){
                sendFollowRequest(idUser: $idUser){
                    success
                    error
                    message
                    followRequest{
                        toFollow{
                            username
                        }
                        status
                    }
                }
            }
            ''',
            headers=header,
            variables={'idUser': user_foll.id}
        )
        compare = {"data":{"sendFollowRequest":{"success":True,"error":None,"message":"Request send","followRequest":{"toFollow":{"username":"usertest2"},"status":"PENDING"}}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)
    
    def test_response_follow_request(self):
        user = User.objects.get(email="test1@test1.com")
        f_req = user.follow_recived.first()
        token = get_token(user)
        header = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        response = self.query(
            '''
            mutation responseFollowRequest($idRequest: ID!, $response: Boolean!){
                responseFollowRequest(idRequest: $idRequest, response: $response){
                    success
                    error
                    message
                    followRequest{
                        requester{
                            username
                        }
                        status
                    }
                }
            }
            ''',
            headers=header,
            variables={'idRequest': f_req.id, 'response': True}
        )
        compare =  {"data":{"responseFollowRequest":{"success":True,"error":None,"message":"Follow request accepted","followRequest":{"requester":{"username":"usertest2"},"status":"ACCEPTED"}}}}
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content, compare)

