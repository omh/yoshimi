<!doctype html>
<html ng-app>
<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
    <%block name="headtitle">
        <title>Yoshimi Admin</title>
    </%block>
    <%block name="head">
    </%block>
    <%block name="meta">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </%block>
     <link href='http://fonts.googleapis.com/css?family=Open+Sans:300italic,400italic,400,300,600' rel='stylesheet' type='text/css'>
</head>
<body class="admin">
    <%block name="feedback"/>
    <%block name="flash">
        % if req.session.peek_flash('y.errors'):
            <%include file='_flash.mako' args="queue='y.errors', css_class='error'"/>
        % endif
    </%block>

    ${self.body()}
</body>
</html>
