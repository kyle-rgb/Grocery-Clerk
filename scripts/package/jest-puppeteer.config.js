module.exports = {
	launch: {
		headless: false,
		slowMo: 2000,  
		executablePath: "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
		dumpio: false,
		args: ["--start-maximized","--profile-directory=Profile 1"],
		userDataDir: "C:\\c\\Profiles",
		devtools: false,
		timeout: 0,
		defaultViewport: {
			width: 1920,
			height: 1080
		},
		dumpio: true
	},
	globals: {
		browser: true
	}
};
