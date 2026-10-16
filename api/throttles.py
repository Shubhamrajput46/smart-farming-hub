from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class ApiAnonRateThrottle(AnonRateThrottle):
    scope = "anon"

class ApiUserRateThrottle(UserRateThrottle):
    scope = "user"

class OpenAIUserRateThrottle(UserRateThrottle):
    scope = "openai_user"

class OpenAIAnonRateThrottle(AnonRateThrottle):
    scope = "openai_anon"
