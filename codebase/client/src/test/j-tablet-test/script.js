window.addEventListener("load", function(event) {
        var name = !!localStorage.getItem("username") ? localStorage.getItem("username") : "You";
        var typed = new Typed('#typed', {
                strings: ['Hello,^450 World^300!'],
		typeSpeed: 100,
                startDelay: 500,
		backDelay: 800,
		backSpeed: Math.floor(Math.random() * 100)+50,
	});
});
