
let dropdownMenu = document.querySelector(".dropdown-menu");
let headerRightLink = document.querySelector(".header-right");
let menu = document.querySelector(".menu");
let arrow = document.querySelector(".menu i");
 /*
headerRightLink.addEventListener('mouseover', () => {
    dropdownMenu.style.display = "flex";
    arrow.textContent = "arrow_drop_up";
});

 dropdownMenu.addEventListener('mouseover', () => {
     dropdownMenu.style.display = "flex";
     arrow.textContent = "arrow_drop_up";
 });
 dropdownMenu.addEventListener('mouseleave', () => {
     setTimeout( () => {
         dropdownMenu.style.display = "none";
         arrow.textContent = "arrow_drop_down";
     }, 3000)
 });
*/
 menu.addEventListener("click", () => {
    if (arrow.textContent === "arrow_drop_down"){
        arrow.textContent = "arrow_drop_up";
        dropdownMenu.style.display = "flex";
    }else{
        arrow.textContent = "arrow_drop_down";
        dropdownMenu.style.display = "none";
    }
 })