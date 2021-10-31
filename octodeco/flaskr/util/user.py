# Please see LICENSE.md
from abc import ABC, abstractmethod;
from enum import Enum;
from flask import url_for;


class AllowedFeature(Enum):
    DIVE_VIEW = 101;
    DIVE_MODIFY = 102;

    ADMIN_IS_ADMIN = 201;


class User(ABC):
    @abstractmethod
    def is_logged_in(self):
        pass;

    @abstractmethod
    def user_given_name(self):
        pass;

    @abstractmethod
    def user_picture_url(self):
        pass;

    @abstractmethod
    def user_id(self):
        pass;

    @abstractmethod
    def is_allowed(self, feature, **kwargs):
        pass;

    def is_admin(self):
        return self.is_allowed( AllowedFeature.ADMIN_IS_ADMIN );


class SimpleUser(User):
    def is_logged_in(self):
        return True;

    def user_given_name(self):
        return 'Otto the Octopus';

    def user_picture_url(self):
        return url_for('static', filename = 'images/octopus-white.png');

    def user_id(self):
        return 1;

    def is_allowed(self, feature, **kwargs):
        return True;

    def __str__(self):
        return f'User {self.user_id()}, {self.user_given_name()}';

