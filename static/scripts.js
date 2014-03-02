$(function () {

    //ajax call to edit
    //to_edit is a string that targets data-id
    //id is the data-id of the post    
    function submit_post(to_edit, id){
        $.ajax({
            type: "POST",
            url: "/edit",
            data: JSON.stringify({body: $(to_edit).text(), id: id}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){                
                $(to_edit).text(data.result);
            },
            failure: function() {
                console.log("edit failed on id: " + id);
                }
        });
    }

    //ajax call to delete
    //div is the parent div that needs to be deleted
    function delete_post(div ,id){
        $.ajax({
            type: "POST",
            url: "/delete",
            data: JSON.stringify({id:id}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){                
                $(div).hide("slow");
            },
            failure: function(data){
                console.log("delete failed on id: " + id)
            }
        });
    }

    //ajax call to status
    function change_status(status, instance, id){
        $.ajax({
            type: "POST",
            url: "/status",
            data: JSON.stringify({status: status, id:id}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){
                console.log(status);
                $(instance).parent().parent().prop("class", status); //chaining parents to fetch the grandparent of the element
            },
            failure: function(data){
                console.log("status change failed on id: " + id);
            }

        });

    }
    

    //activates text editing on click   
    $(".activate").click(function () {

        var id = $(this).data("id");
        var to_edit = "p[data-id='" + id + "']";

        $(to_edit).css("background-color", "white");
              
        $(to_edit).prop("contenteditable","true").focus();
        
    });

    //saves text editing
    $(".save").click(function () {
        var id = $(this).data("id");
        var to_edit = "p[data-id='" + id + "']";

        var set_color = $(to_edit).closest("div").css("background-color");
        $(to_edit).css("background-color", set_color);

        submit_post(to_edit, id);
    });

    //deletes entry
    $(".delete").click(function () {
        var id = $(this).data("id");
        var to_edit = "p[data-id='" + id + "']";

        var parent = $(to_edit).parent();

        delete_post(parent, id);

    });

    //TODO SKRIPTA ZA MJENJANJE STATUSA

    $(".toTODO, .toWIP, .toDONE").click(function () {

        var id = $(this).data("id");
        var status = $(this).text();        
        change_status(status, this, id);

    });
   
});