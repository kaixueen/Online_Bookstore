$(document).ready(function () {
    // Bind click event to Add to Cart buttons
    $("body").on("click", ".btn-add-cart", function (event) {

        event.preventDefault();
        var bookId = $(this).data("book-id");

        $.ajax({
            url: "/add_to_cart/" + bookId,
            method: "GET", 
            success: function (data) {
                $("#snackbar").html("Added to Cart!");
                var x = document.getElementById("snackbar");
                x.className = "show";
                setTimeout(function () {
                    x.className = x.className.replace("show", "");
                }, 1000);

                $("#gettotalcart").html(data.total_items);
                console.log("Total cart updated:", data.total_items);
            },
            error: function (xhr, status, error) {
                console.error("Failed to add to cart:", error);
            }
        });
    });
});
