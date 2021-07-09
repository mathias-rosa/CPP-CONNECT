 
 let dropdownMenu = document.querySelector(".dropdown-menu");
 let headerRightLink = document.querySelector(".header-right #profile");

 headerRightLink.addEventListener('mouseover', () => {
     
    dropdownMenu.style.display = "flex";
});

 dropdownMenu.addEventListener('mouseover', () => {
     dropdownMenu.style.display = "flex";
 });
 dropdownMenu.addEventListener('mouseleave', () => {
     setTimeout( () => {
         dropdownMenu.style.display = "none";
     }, 3000)
 });