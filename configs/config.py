class Config:
    TOKEN= "REMEMBER TO SIGN UP AWS API Gateway"
    __access_key_id = "REMEMBER TO SIGN UP AWS API Gateway"
    __access_key_secret = "REMEMBER TO SIGN UP AWS API Gateway"

    MIN_SLEEP=1
    MAX_SLEEP=10

    mongodb_host = 'localhost'
    mongodb_port = 27017

    check_const = "Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that."
    def get_token(self):
        return self.TOKEN
    
    def get_aws_access_key_id(self):
        return self.__access_key_id
    
    def get_aws_access_key_secret(self):
        return self.__access_key_secret
    