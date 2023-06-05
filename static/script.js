'use strict';
window.addEventListener('load', function () {
  document.getElementById('sign-out').onclick = function () {
    firebase.auth().signOut().then(function(){
      window.location.replace("/")
    });
  };

  var uiConfig = {
    signInSuccessUrl: '/',
    signInOptions: [firebase.auth.EmailAuthProvider.PROVIDER_ID]
  };

  firebase.auth().onAuthStateChanged(function (user) {
    if (user) {
      document.getElementById('user-info').hidden = false;
      document.getElementById('login-info').hidden = false;
      console.log('Signed in as ${user.displayName} (${user.email})');
      user.getIdToken().then(function (token) {
        //document.cookie = "token=" + token;
        document.cookie = "token=" + token + ";path=/";

      });
    } else {
      var ui = new firebaseui.auth.AuthUI(firebase.auth());
      ui.start('#firebase-auth-container', uiConfig);
      document.getElementById('user-info').hidden = true;
      document.getElementById('login-info').hidden = true;
      //document.cookie = "token=";
      document.cookie = "token=;path=/";

    }
  }, function (error) {
    console.log(error);
    alert('Unable to log in: ' + error);
  });

});


