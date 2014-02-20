/*        $("div").prop("contenteditable","true");
    });
*/

$(function(){    
    $(".activate").click(function(){
        var check = $(this).data("id");
        var to_edit = "[data-id='" + check + "']";
              
        $("p" + to_edit).prop("contenteditable","true");
    });
});