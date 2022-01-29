$(document).ready(function() {
  /* Date */
  date = new Date();

  time = date.toLocaleString("en-US", {
    hour: "numeric",
    minute: "numeric",
    hour12: true,
  });
  date = date.toLocaleString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
      timeZoneName: "short"
  })
  document.getElementById("date").innerHTML = date;
  document.getElementById("time").innerHTML = time;

  /*Alert Error first */
  error_message_container = document.getElementById("errorMessage");
  if (error_message_container.value) {
    alert(error_message_container.value);
  }
  loadPortfolioNames();
  /* Getting Symnbol Names */
  emptyState();
  datalist = document.getElementById("symbols");
  fetch("/symbols", { mode: "no-cors" })
    .then((response) => response.json())
    .then((data) => {
      data.map((symbol) => {
        opt = document.createElement("option");
        opt.innerHTML = symbol;
        whitespaceIndex = symbol.indexOf(" ");
        if (whitespaceIndex != -1) {
          opt.value = symbol.substring(0, whitespaceIndex);
        } else {
          opt.value = symbol;
        }
        datalist.appendChild(opt);
      });
    });

  /* Enable calculate button if portfolio is selected otherwise disable */
  $('#portfolios').change(function(event) { 
    if (event.target.value == "") {
        emptyState();
      } else {
        readyState(event);
      }
  })
  setTimeout(() => {
    $('#portfolios').val('Retirement').trigger('change')
  }, 1000)



  /* Adding year options from 1 to 40 */
  var min = 1,
    max = 40,
    select = document.getElementById("years");
  for (var i = min; i <= max; i++) {
    var opt = document.createElement("option");
    opt.value = i;
    opt.innerHTML = i;
    if (i == 40) {
      opt.setAttribute("selected", "");
    }
    select.appendChild(opt);
  }

  /* Cash mode and stock mode toggler */
  stockMode = document.getElementById("stockMode");
  cashMode = document.getElementById("cashMode");
  stockBuyCount = document.getElementById("stockBuyCount");
  stockPrice = document.getElementById("stockPrice");
  cash = document.getElementById("cash");

  let rad = document.forms[3].modes;
  for (let i = 0; i < rad.length; i++) {
    rad[i].addEventListener("change", function () {
      if (rad[i].value == "share") {
        stockMode.style.display = "flex";
        cashMode.style.display = "none";
        stockPrice.setAttribute("required", "");
        stockPrice.removeAttribute("disabled");
        stockBuyCount.removeAttribute("disabled");
        stockBuyCount.setAttribute("required", "");
        cash.removeAttribute("required");
        cash.setAttribute("disabled", "");
      } else {
        stockMode.style.display = "none";
        cashMode.style.display = "flex";
        stockBuyCount.removeAttribute("required");
        stockBuyCount.setAttribute("disabled", "");
        stockPrice.removeAttribute("required");
        stockPrice.setAttribute("disabled", "");
        cash.setAttribute("required", "");
        cash.removeAttribute("disabled");
      }
    });
  }

  /* Adding portfolio */
  addPortfolioForm = document.getElementById("addPortfolioForm");
  addPortfolioForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new URLSearchParams();
    data.append(
      event.target.elements.portfolioName.name,
      event.target.elements.portfolioName.value
    );
    data.append(
      event.target.elements.deposit.name,
      event.target.elements.deposit.value
    );
    init = {
      method: "POST",
      body: data,
      mode: "no-cors",
    };
    fetch("/portfolio/add", init)
      .then((response) => response.json())
      .then((data) => {
        if (data["is_success"] == false) {
          alert("Unabled to add portfolio: " + data["message"]);
        } else {
          alert("Porfolio is added successfully");
          $("#addPortfolioModal").modal("hide");
          loadPortfolioNames();
        }
      });
  });

  /* Deleting Portfolio */
  deletePortfolioForm = document.getElementById("deletePortfolioForm");
  deletePortfolioForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new URLSearchParams();
    data.append(
      event.target.elements.portfolioName.name,
      event.target.elements.portfolioName.value
    );
    init = {
      method: "POST",
      body: data,
      mode: "no-cors",
    };
    fetch("/portfolio/delete", init)
      .then((response) => response.json())
      .then((data) => {
        if (data["is_success"] == false) {
          alert("Unabled to delete portfolio: " + data["message"]);
        } else {
          alert("Porfolio is deleted successfully");
          $("#deletePortfolioModal").modal("hide");
          loadPortfolioNames();
          emptyState();
        }
      });
  });

  /* Adding funds to portfolio */
  addFundsForm = document.getElementById("addFundsForm");
  addFundsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    portfolioNameHidden = document.getElementById("portfolioNameHidden");
    if (portfolioNameHidden == "") {
      alert("Please select a portfolio");
      return False;
    }
    const data = new URLSearchParams();
    data.append("deposit", event.target.elements.deposit.value);
    data.append("portfolioName", portfolioNameHidden.value);
    init = {
      method: "POST",
      body: data,
      mode: "no-cors",
    };

    fetch("/portfolio/funds/add", init)
      .then((response) => response.json())
      .then((data) => {
        if (!data["is_success"]) {
          alert("Unabled to add funds: " + data["message"]);
        } else {
          alert("Funds is added successfully");
          updateCashState(portfolioNameHidden.value);
          $("#addFundsModal").modal("hide");
          emptyState();
          loadPortfolioNames();
        }
      });
  });
  if (document.getElementById("isCalculated").value == "true") {
    prevPortfolio = document.getElementById("prevPortfolio");
    portfolio = document.getElementById("portfolios");
    portfolio.value = prevPortfolio.value;
    document.getElementById("funds").innerHTML =
      document.getElementById("prevFunds").value;
    document.getElementById("symbolInput").value =
      document.getElementById("prevSymbol").value;
    document.getElementById("cash").value =
      document.getElementById("prevCash").value;
    document.getElementById("commission").value =
      document.getElementById("prevCommission").value;
    document.getElementById("years").value =
      document.getElementById("prevYear").value;
    if (document.getElementById("prevMode").value == "share") {
      $("#radio2").click();
      document.getElementById("stockBuyCount").value =
        document.getElementById("prevStockBuyCount").value;
      document.getElementById("stockPrice").value =
        document.getElementById("prevStockPrice").value;
    }
  }
  

});

function reloadSelectPortfolio(portfolioNames) {
  portfoliosSelect = document.getElementById("portfolios");
  for (const i in portfoliosSelect.options) {
    portfoliosSelect.options.remove(i);
  }
  const defaultOpt = document.createElement("option");
  defaultOpt.value = "";
  defaultOpt.innerHTML = "Select Portfolio";
  portfoliosSelect.options.add(defaultOpt);
  for (const i in portfolioNames) {
    var opt = document.createElement("option");
    opt.value = portfolioNames[i];
    opt.innerHTML = portfolioNames[i];
    portfoliosSelect.options.add(opt);
  }
}

function emptyState() {
  document.getElementById("calculateBtn").setAttribute("disabled", "");
  document.getElementById("addFundsButton").setAttribute("disabled", "");
  document.getElementById("deletePortfolioButton").setAttribute("disabled", "");
  document.getElementById("stockPrice").setAttribute("disabled", "");
  document.getElementById("stockBuyCount").setAttribute("disabled", "");
  document.getElementById("buyBtn").setAttribute("disabled", "");
  document.getElementById("toDeletePortfolioField").value = "";
  document.getElementById("funds").innerHTML = "N/A";
}

function readyState(event) {
  document.getElementById("calculateBtn").removeAttribute("disabled");
  document.getElementById("buyBtn").removeAttribute("disabled");
  document.getElementById("addFundsButton").removeAttribute("disabled");
  document.getElementById("deletePortfolioButton").removeAttribute("disabled");
  document.getElementById("toDeleteMessage").innerHTML =
    "Are you sure you want to delete " + event.target.value;
  document.getElementById("portfolioNameHidden").value = event.target.value;
  document.getElementById("toDeletePortfolioField").value = event.target.value;
  updateCashState(document.getElementById("portfolioNameHidden").value);
}

function updateCashState(portfolioName) {
  const data = new URLSearchParams();
  data.append("portfolioName", portfolioName);
  init = {
    method: "POST",
    body: data,
    mode: "no-cors",
  };
  cashBalance = document.getElementById("funds");
  fetch("/portfolio/funds/get", init)
    .then((response) => response.json())
    .then((data) => {
      if (!data["is_success"]) {
        cashBalance.innerHTML = "N/A";
      } else {
        const options = { 
          minimumFractionDigits: 2,
          maximumFractionDigits: 2 
        };
        cashBalance.innerHTML = '$' + Number(data["funds"]).toLocaleString('en', options);
      }
    });
}

function loadPortfolioNames() {
  fetch("/portfolio/names", { method: "GET", mode: "no-cors" })
    .then((response) => response.json())
    .then((data) => {
      document.forms[0].portfolioName.value = "";
      reloadSelectPortfolio(data);
    });
}

function validateForm(form) {
  formData = new FormData(form);
  for (var pair of formData.entries()) {
    if (pair[1] == "") {
      alert("There is an empty field");
      return false;
    }
  }
  return true;
}

