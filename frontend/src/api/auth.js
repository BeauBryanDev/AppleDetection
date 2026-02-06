import client from './axios';

export const loginRequest = async (email, password) => {
  //  OAuth2 requiere que los datos se envíen como application/x-www-form-urlencoded
  
  const params = new URLSearchParams();
  params.append('username', email); // OAuth2 SIEMPRE exige que el campo se llame 'username'
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