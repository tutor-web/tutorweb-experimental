<!DOCTYPE html>
<html lang="en">
<head>
  <title>Tutorweb: Register</title>
  <meta http-equiv="X-UA-Compatible" content="IE=EDGE" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="/css/libraries.min.css" />
  <link rel="stylesheet" type="text/css" href="/css/index.min.css" />
  <link rel="stylesheet" type="text/css" href="/api/static/css/form.css" />

  <link rel="shortcut icon" href="/images/tutor-favicon.ico" />
  <link rel="icon" sizes="76x76" href="/images/apple-touch-icon-ipad-76x76.png" />
  <link rel="icon" sizes="152x152" href="/images/apple-touch-icon-ipad-retina-152x152.png" />
  <link rel="icon" sizes="60x60" href="/images/apple-touch-icon-iphone-60x60.png" />
  <link rel="icon" sizes="120x120" href="/images/apple-touch-icon-iphone-retina-120x120.png" />
  <link rel="apple-touch-icon" sizes="76x76" href="/images/apple-touch-icon-ipad-76x76.png" />
  <link rel="apple-touch-icon" sizes="152x152" href="/images/apple-touch-icon-ipad-retina-152x152.png" />
  <link rel="apple-touch-icon" sizes="60x60" href="/images/apple-touch-icon-iphone-60x60.png" />
  <link rel="apple-touch-icon" sizes="120x120" href="/images/apple-touch-icon-iphone-retina-120x120.png" />
</head>

<body>

  <main role="main" class="container">
    <h1 class="text-center"><a href="/"><img src="/images/logo.jpg" alt="Tutor web" /></a></h1>

    <section>
      <h3>Register</h3>
      ${form|n}
    </section>

    <div class="status">
      <div id="tw-actions">
        <label class="button" for="deformsubmit">Register</label>
        <style>#deformsubmit { display: none }</style>
        <a href="${request.route_url('auth_activate_request_code')}" class="button">Reset your password</a>
        <a href="/" class="button">Back</a>
      </div>
    </div>
  </main>
</body>
</html>
