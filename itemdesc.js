let img = document.querySelector('img');
let btn1 = document.querySelector('#btn1');
let btn2= document.querySelector('#btn2');
let btn3 = document.querySelector('#btn3');

btn1.addEventListener('click', ()=> {
	img.src = '1.jpg';
})
btn2.addEventListener('click', ()=> {
	img.src = '2.jpg';
})
btn3.addEventListener('click', ()=> {
	img.src = '3.jpg';
})

