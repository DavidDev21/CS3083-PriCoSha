
// submits the form data and then reset the input fields
function handleSubmit(){
    
    let form = document.getElementById('login-form')

    form.submit()
    form.reset()
}

// Support to force reload the page?
// window.addEventListener( "pageshow", function ( event ) {
//     var historyTraversal = event.persisted || 
//                            ( typeof window.performance != "undefined" && 
//                                 window.performance.navigation.type === 2 );
//     if ( historyTraversal ) {
//       // Handle page restore.
//       window.location.reload();
//     }
//   });