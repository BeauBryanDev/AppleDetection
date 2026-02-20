import client from './axios';

export const checkEmailExists = async (email) => {
  return client.post('/auth/check-email', null, {
    params: { email }
  });
};

export const loginRequest = async (email, password) => {
  //  OAuth2 data to be sent as :: application/x-www-form-urlencoded
  
  const params = new URLSearchParams();
  params.append('username', email); //  username is the email

  params.append('password', password);

  return client.post('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });

};

export const registerRequest = async (userData) => {
  return client.post('/users/signup', userData);
};

export const verifyTokenRequest = async () => {
  return client.get('/users/me');
};