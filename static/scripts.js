$(function() {
    /* GLOBALS */
    //list id is the same for all posts and actions, so it can be global and loaded once
    var GLOBAL_LIST_ID = $(".container").data("list-id");
    /* AJAX */
    //ajax call to delete_post
    //div is the parent div that needs to be deleted
    function delete_post(target, id) {
        $.ajax({
            type: "POST",
            url: "/" + GLOBAL_LIST_ID + "/delete_post",
            data: JSON.stringify({
                id: id
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                $(target).hide("slow");
            },
            failure: function(data) {
                console.log("delete failed on id: " + id);
            }
        });
    }

    //ajax call to status
    function change_status(status, target, id) {
        $.ajax({
            type: "POST",
            url: "/" + GLOBAL_LIST_ID + "/status",
            data: JSON.stringify({
                status: status,
                id: id
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                $(target).prop("class", 'col-sm-3 ' + status + ' activate');
            },
            failure: function(data) {
                console.log("status change failed on id: " + id);
            }
        });
    }
    /* EVENT HANDLERS */
    //activates text editing on click, jeditable does the ajax call
    $(".activate").click(function() {
        var id = $(this).closest("div").data("id");
        var target = "div[data-id='" + id + "'] .editable";
        //$(target).css("background-color", "white");
        $(target).editable('/' + GLOBAL_LIST_ID + '/edit', {
            type: 'textarea',
            cancel: 'Cancel',
            submit: 'Save',
            tooltip: 'click to edit',
            rows: 4,
            submitdata: {
                post_id: id,
            },
            data: function(value, settings) {
                var br2nl = value.replace(/<br[\s\/]?>/gi, '\n');
                return br2nl;
            }
        });
    });
    //deletes post entry
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
            $("#post_area").show("slow");
            post_shown = true;
        } else {
            $(this).text("Add post");
            $("#post_area").hide("slow");
            post_shown = false;
        }
    });
    //sorting dropdown
    $("#list-select").change(function() {
        $("#list-select option:selected").each(function (){
            if( $(this).text() == "Sort by Date (desc)"){
                $(".activate").tsort({order: 'desc', data: 'id'});
            }
            if( $(this).text() == "Sort by Date (asc)"){
                $(".activate").tsort({order: 'asc', data: 'id'});
            }
            if( $(this).text() == "Sort by Author"){
                $(".activate").tsort({data: 'author'});
            }
        });
    });
});

