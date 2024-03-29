document.addEventListener("DOMContentLoaded", function() {
    const accordionItems = document.querySelectorAll('.accordion h3');
    let mainParent;
    let answer;

    accordionItems.forEach(item => {
        item.addEventListener('click', () => {
            answer = item.nextElementSibling;
            mainParent = item.parentElement;
            if (mainParent.classList.contains('active')) {
                mainParent.classList.remove('active');
                answer.style.maxHeight = `0px`;
            } else { 
                mainParent.classList.add('active');
                answer.style.maxHeight = `1000px`; // Set a large enough value
            }
        });
    });
});
      document.getElementById('newAcc').addEventListener('click', function() {
    // Redirect to the /login URL
    window.location.href = '/register';
  });


     document.getElementById('logIn').addEventListener('click', function() {
    // Redirect to the /login URL
    window.location.href = '/login';
  });

  if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
  }

  function closeAlert(alertId) {
    // Find the alert element by ID
    var alertElement = document.getElementById(alertId);

    // Check if the alert element exists
    if (alertElement) {
      // Hide the alert element by setting its display property to 'none'
      alertElement.style.display = 'none';
    }
  }

  function successCallback(token){
    debugger;
  }
