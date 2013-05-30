$().ready(function() {
    $("div#switcher.iphone a").click(function(){
        $("div#iphone img").attr("src", this.href);
        $(this).addClass("active").siblings("a").removeClass("active");
        return false;
    });
});

$().ready(function() {
    $("div#switcher.android a").click(function(){
        $("div#android img").attr("src", this.href);
        $(this).addClass("active").siblings("a").removeClass("active");
        return false;
    });
});