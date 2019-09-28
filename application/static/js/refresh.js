    $(function () {
        setInterval(refresh, 1000);

        function refresh() {
            $.ajax({
                url: "/refresh_notification",
                type: "POST",
                dataType: "json",
                success: function (data) {
                    if (data[0] > 0) {
                        var message = document.getElementById("message");
                        if (message.hasChildNodes()) {
                            message.removeChild(message.childNodes[0]);
                        }
                        message.innerHTML = "Messages  " + "<span class=\"badge badge-pill badge-danger\">" + data[0] + "</span>"
                    }

                }
            })
        }
    })
