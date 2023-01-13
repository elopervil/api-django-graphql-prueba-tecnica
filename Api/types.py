import graphene
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from graphql_jwt.shortcuts import get_token

from .models import User, Idea, FollowRequest


# Types

class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)

class IdeaType(DjangoObjectType):
    class Meta:
        model = Idea

class FollowRequestType(DjangoObjectType):
    class Meta:
        model = FollowRequest

# User Queries

class UserQuery(graphene.ObjectType):
    users = graphene.List(UserType)
    me = graphene.Field(UserType)
    search_users = graphene.List(UserType, username=graphene.String(required=True))

    def resolve_users(self, info):
        return User.objects.all()
    
    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('User not logged in')
        return user

    def resolve_search_users(self, info, username):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged in')
        return User.objects.filter(username__icontains=username).exclude(pk=user.id)
    
    
# User Mutation

class Register(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    user = graphene.Field(UserType)
    token = graphene.String()
    success = graphene.Boolean()
    error = graphene.List(graphene.String)

    def mutate(self, info, username, email, password):
            try:
                user = User.objects.create(username=username, email=email)
                user.set_password(password)
                user.save()
                token = get_token(user)
                return Register(user=user, token=token, success=True)
            except ValidationError as err:
                return Register(success=False, error=err)

class ChangePassword(graphene.Mutation):
    class Arguments:
        password = graphene.String(required=True)
    
    success = graphene.Boolean()
    error = graphene.List(graphene.String)

    def mutate(self, info, password):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to change your password')
        try:
            user.set_password(password)
            user.save()
            return ChangePassword(success=True)
        except ValidationError as err:
            return ChangePassword(success=False, error=err)

class DeleteFollow(graphene.Mutation):
    class Arguments:
        id_user = graphene.ID(required=True)
    
    success = graphene.Boolean()
    error = graphene.List(graphene.String)
    message = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, id_user):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged in for this')
        try:
            follow = get_object_or_404(User, pk=id_user)
            user.following.remove(follow)
            return DeleteFollow(success=True, message=f'Unfollow {follow.username}')
        except ValidationError as err:
            return DeleteFollow(success=False, error=err)

class DeleteFollower(graphene.Mutation):
    class Arguments:
        id_user = graphene.ID(required=True)
    
    success = graphene.Boolean()
    error = graphene.List(graphene.String)
    message = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, id_user):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged in for this')
        try:
            follower = get_object_or_404(User, pk=id_user)
            user.followers.remove(follower)
            return DeleteFollower(success=True, message=f'{follower.username} removed from follower list')
        except ValidationError as err:
            return DeleteFollower(success=False, error=err)

class UserMutation (graphene.ObjectType):
    register = Register.Field()
    change_password = ChangePassword.Field()
    unfollow = DeleteFollow.Field()
    remove_follower = DeleteFollower.Field()


# Idea Queries

class IdeaQuery(graphene.ObjectType):
    list_all_ideas = graphene.List(IdeaType)
    list_my_ideas = graphene.List(IdeaType)
    list_followed_ideas = graphene.List(IdeaType, id_user=graphene.ID(required=True))

    def resolve_list_all_ideas(self, info):
        return Idea.objects.all().exclude(visibility='private')

    def resolve_list_my_ideas(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to see your ideas')
        return Idea.objects.filter(pub_user=user)
    
    def resolve_list_followed_ideas(self, info, id_user):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged in')
        try:
            followed_user = get_object_or_404(User, pk = id_user)
            if user.following.filter(pk=followed_user.id).exists():
                return followed_user.idea_user.exclude(visibility=Idea.PRIVATE)
            else:
                return followed_user.idea_user.filter(visibility=Idea.PUBLIC)
        except ValidationError as err:
            raise GraphQLError('Error')


# Idea Mutation

class AddIdea(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        visibility = graphene.String(required=False)
    
    idea = graphene.Field(IdeaType)
    success = graphene.Boolean()
    error = graphene.List(graphene.String)

    def mutate(self, info, content, **kwargs):
        visibility = kwargs.get('visibility', None)
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to add ideas')
        try:
            if visibility:
                idea = Idea.objects.create(content=content, visibility=visibility.lower(), pub_user=user)
                idea.save()
            else:
                idea = Idea.objects.create(content=content, pub_user=user)
                idea.save()
            return AddIdea(success=True, idea=idea)
        except ValidationError as err:
            return AddIdea(success=False, error=err)


class EditIdea(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        content = graphene.String(required=False)
        visibility = graphene.String(required=False)
    
    idea = graphene.Field(IdeaType)
    success = graphene.Boolean()
    error = graphene.List(graphene.String)

    def mutate(self, info, id, **kwargs):
        content = kwargs.get('content', None)
        visibility = kwargs.get('visibility', None)
        user = info.context.user

        if user.is_anonymous:
            raise GraphQLError('You must be logged to edit your ideas')
        
        try:
            idea_qs = Idea.objects.filter(pub_user=user)
            edit_idea = get_object_or_404(idea_qs, pk=id)
            if content:
                edit_idea.content=content
            if visibility:
                edit_idea.visibility=visibility.lower()
            edit_idea.save()
            return EditIdea(success=True, idea=edit_idea)
        except ValidationError as err:
            return EditIdea(success=False, error=err)


class DeleteIdea(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    error = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info, id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to delete your ideas')
        try:
            idea_qs = Idea.objects.filter(pub_user=user)
            idea = get_object_or_404(idea_qs, pk=id)
            idea.delete()
            return DeleteIdea(success=True, message='Delete success')
        except ValidationError as err:
            return DeleteIdea(success=False, error=err, message='Delete not success')


class IdeaMutation(graphene.ObjectType):
    add_idea = AddIdea.Field()
    edit_idea = EditIdea.Field()
    delete_idea = DeleteIdea.Field()


# FollowRequest Queries

class FollowRequestQuery(graphene.ObjectType):
    follow_up_request = graphene.List(FollowRequestType)

    def resolve_follow_up_request(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to see your follow request list')
        return user.follow_recived.all()


# FollowRequest Mutation

class SendFollowRequest(graphene.Mutation):
    class Arguments:
        id_user = graphene.ID(required=True)
    
    success = graphene.Boolean()
    error = graphene.List(graphene.String)
    message = graphene.String()
    follow_request = graphene.Field(FollowRequestType)

    def mutate(self, info, id_user):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to follow user')
        try:
            users = User.objects.all()
            to_follow = get_object_or_404(users, pk=id_user)
            follow_request = FollowRequest.objects.create(requester=user, to_follow=to_follow)
            follow_request.save()
            return SendFollowRequest(success=True, message='Request send', follow_request=follow_request)
        except ValidationError as err:
            return SendFollowRequest(success=False, error=err)

class ResponseFollowRequest(graphene.Mutation):
    class Arguments:
        id_request = graphene.ID(required=True)
        response = graphene.Boolean(required=True)
    
    success = graphene.Boolean()
    error = graphene.List(graphene.String)
    message = graphene.String()
    follow_request = graphene.Field(FollowRequestType)

    def mutate(self, info, id_request, response):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged for this')
        try:
            list_request = user.follow_recived.all()
            req = get_object_or_404(list_request, pk=id_request)
            req_user = req.requester
            if response:
                req.status = FollowRequest.ACCEPTED
                req.save()
                req_user.following.add(user)
                req_user.save()
                return ResponseFollowRequest(success=True, message='Follow request accepted', follow_request=req)
            else:
                req.status = FollowRequest.DENIED
                req.save()
                return ResponseFollowRequest(success=True, message='Follow request denied', follow_request=req)
        except ValidationError as err:
            return ResponseFollowRequest(success=False, error=err)

class FollowRequestMutation(graphene.ObjectType):
    send_follow_request = SendFollowRequest.Field()
    response_follow_request = ResponseFollowRequest.Field()
    

