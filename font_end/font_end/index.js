window.addEventListener('DOMContentLoaded', function() {
  new CozeWebSDK.WebChatClient({
    config: {
      type: 'bot',
      bot_id: '7519370550456975401',
      isIframe: false,
    },
    auth: {
      type: 'token',
      token: 'your_token_here',
      onRefreshToken: async () => 'your_token_here'
    },
    userInfo: {
      id: 'user',
      url: './logo/10kv.png',
      nickname: 'User',
    },
    ui: {
      base: {
        icon: './logo/10kv.png',
        layout: 'pc',
        lang: 'en',
        zIndex: 1000
      },
      header: {
        isShow: true,
        isNeedClose: true,
      },
      asstBtn: {
        isNeed: false
      },
      footer: {
        isShow: true,
        expressionText: 'Powered by ...',
      },
      chatBot: {
        title: 'BuEMO',
        uploadable: true,
        width: 390,
        el: document.getElementById('coze-chat')
      },
    },
  });
}); 