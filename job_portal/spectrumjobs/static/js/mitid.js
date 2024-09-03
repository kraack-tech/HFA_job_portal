/* Criipto object */
/* Reference: "Criipto Documentation", Criipto, https://docs.criipto.com/verify/integrations/javascript/, https://github.com/criipto/criipto-auth.js */
var criiptoAuth = new CriiptoAuth({
  domain: 'userauth2-test.criipto.id',
  clientID: 'urn:my:application:identifier:491761',
  store: sessionStorage,
});