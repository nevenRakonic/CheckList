$(function() {
    //ajax call to edit
    //to_edit is a string that targets data-id
    //id is the data-id of the post    
    function submit_post(target, id) {
        $.ajax({
            type: "POST",
            url: "/edit",
            data: JSON.stringify({
                body: $(target + " p:first-child").html(),
                id: id
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                $(target + " .post_content").load("/" + id + "/show_post");
            },
            failure: function() {
                console.log("edit failed on id: " + id);
            }
        });
    }
    //ajax call to delete
    //div is the parent div that needs to be deleted
    function delete_post(target, id) {
        $.ajax({
            type: "POST",
            url: "/delete",
            data: JSON.stringify({
                id: id
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                $(target).hide("slow");
            },
            failure: function(data) {
                console.log("delete failed on id: " + id)
            }
        });
    }
    //ajax call to status
    function change_status(status, target, id) {
        $.ajax({
            type: "POST",
            url: "/status",
            data: JSON.stringify({
                status: status,
                id: id
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                $(target).prop("class", status);
            },
            failure: function(data) {
                console.log("status change failed on id: " + id);
            }
        });
    }
    /* EVENT HANDLERS */
    //control variable for editing process
    var in_edit;
    //activates text editing on click   
    $(".activate").click(function() {
        var id = $(this).closest("div").data("id");
        var target = "div[data-id='" + id + "'] p:first-child";
        //$(target).css("background-color", "white");
        $(target).editable('/edit', {
            type: 'textarea',
            cancel: 'Cancel',
            submit: 'OK',
            tooltip: 'click to edit',
            submitdata: {
                post_id: id
            },
            data: function(value, settings) {
                var br2nl = value.replace(/<br[\s\/]?>/gi, '\n');
                return br2nl;
            }
        });        
    });
    //saves text editing
    /*
    $(".save").click(function() {
        if (in_edit) {
            var id = $(this).closest("div").data("id");
            var target = "div[data-id='" + id + "']";            
            submit_post(target, id);
            in_edit = false;
        }
    });*/
    //deletes entry
    $(".delete").click(function() {
        var id = $(this).closest("div").data("id");
        var target = "div[data-id='" + id + "']";
        delete_post(target, id);
    });
    //changes post status
    $(".toTODO, .toWIP, .toDONE").click(function() {
        var id = $(this).closest("div").data("id");
        var target = "div[data-id='" + id + "']";
        var status = $(this).text();
        change_status(status, target, id);
    });
    //hides initial post area
    $("#post_area").hide();
    //control variable for add post event handler
    var post_shown;
    //add entry form
    $("#add_post").click(function() {
        if (!post_shown) {
            $(this).text("Hide add post");
            $("#post_area").show();
            post_shown = true;
        } else {
            $(this).text("Add post");
            $("#post_area").hide();
            post_shown = false;
        }
        //texteditor
        //tinymce.init({
        //    selector: 'textarea.tinyMCE'
        //});
    });
});