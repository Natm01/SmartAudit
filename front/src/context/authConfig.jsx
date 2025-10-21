export const msalConfig = {
  auth: {
    clientId: "4950cdc1-22b8-4962-a333-6d168a572985",
    authority: "https://login.microsoftonline.com/a8803954-c6a6-4d60-b4e1-d78ecb2ca82a",
    redirectUri: window.location.origin // Sin /auth/callback
  }
};

export const loginRequest = {
  scopes: ["openid", "profile", "email"]
};