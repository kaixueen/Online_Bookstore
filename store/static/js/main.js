$(document).ready(function () {
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
            error: function (xhr) {
                if (xhr.status === 401 && xhr.responseJSON?.login_required) {
                    window.location.href = "/login?next=/add_to_cart/" + bookId;
                } else {
                    console.error("Failed to add to cart:", xhr.responseText);
                }
            }
        });
    });
});
