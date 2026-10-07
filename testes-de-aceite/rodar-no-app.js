// ═════════════════════════════════════════════════════════════════
//  Testes de aceite — roda no APP DE REFERÊNCIA (aba aberta e logada).
//  Uso: abrir o app, F12 › Console, colar este arquivo inteiro e Enter.
//  Ele lê casos.json (servido junto) ou usa window.CASOS_ACEITE, roda as
//  funções atuais e imprime OK/FALHOU. Não grava nada no banco: os
//  parâmetros alterados são restaurados no fim.
// ═════════════════════════════════════════════════════════════════
(async function(){
  const C = window.CASOS_ACEITE || await fetch("testes-de-aceite/casos.json").then(r=>r.json());
  const perto=(a,b)=> typeof a==="number" && typeof b==="number" ? Math.abs(a-b) < 0.005 : JSON.stringify(a)===JSON.stringify(b);
  const confere=(obtido, esperado)=>{
    if(esperado && typeof esperado==="object" && !Array.isArray(esperado)){
      const dif=[]; Object.keys(esperado).forEach(k=>{ if(!perto(obtido&&obtido[k], esperado[k])) dif.push(k+": obtido "+JSON.stringify(obtido&&obtido[k])+", esperado "+JSON.stringify(esperado[k])); });
      return dif;
    }
    return perto(obtido, esperado) ? [] : ["obtido "+JSON.stringify(obtido)+", esperado "+JSON.stringify(esperado)];
  };
  const bkJanela=PARAM_JANELA, bkOCX=OCX, catTeste="TESTE ACEITE", tinhaCat=Object.prototype.hasOwnProperty.call(SLA_DATA, catTeste);
  PARAM_JANELA=Object.assign({}, JANELA_PAD, { meses:{} });
  try{ if(typeof slaCacheLimpar==="function") slaCacheLimpar(); }catch(e){}
  const res=[];
  try{
    for(const c of C.casos){
      let obtido, e=c.entrada;
      try{
        if(c.funcao==="janelaDoMes") obtido=janelaDoMes(e.mes);
        else if(c.funcao==="janelaAprovEstimada") obtido=janelaAprovEstimada(e.criacao);
        else if(c.funcao==="calcSLAStatus") obtido=calcSLAStatus(e.inicio, e.sla, e.dataOC);
        else if(c.funcao==="vbSaldoLinha"){ const r=[0,"",""," ",e.orcado,e.saldo!=null?e.saldo:null,e.realizado,e.comprometido]; obtido=vbSaldoLinha(r); }
        else if(c.funcao.indexOf("ocxPrecoRef")===0){
          const mk=(x)=>({ col:"999", oc:x.oc, tmv:"1.1.12", cod:"TESTE-ACEITE", ins:"ITEM TESTE ACEITE", und:"UN", qtd:x.qtd, preco:x.preco, valor:x.qtd*x.preco, dEmiOC:x.data, dCriOC:x.data, canc:false, scs:[] });
          OCX=e.historico.map(mk).concat([mk(e.nova)]);
          const nova=OCX[OCX.length-1], r=ocxPrecoRef(nova), a=ocxPrecoAlto(nova);
          obtido={ media:r&&r.media, n:r&&r.n, ultimo:r&&r.ultimo, alertaPct:a&&a.pct };
        }
        else if(c.funcao==="croCalc"){
          const k=e.categoriaSLA; SLA_DATA[k.nome]={ sup:k.sup, ent:k.ent, total:k.total };
          const it=Object.assign({ id:"teste", col:"999", desc:"TESTE", ativSla:k.nome, scs:"", pedidos:"" }, e.item);
          obtido=croCalc(it);
        }
        else if(c.funcao==="pzMesclar") obtido=pzMesclar(e.base, e.local, e.servidor);
        else { res.push([c.id,"SEM EXECUTOR",[]]); continue; }
        const d=confere(obtido, c.esperado); res.push([c.id, d.length?"FALHOU":"OK", d]);
      }catch(err){ res.push([c.id,"ERRO",[String(err&&err.message||err)]]); }
    }
  } finally {
    PARAM_JANELA=bkJanela; OCX=bkOCX; if(!tinhaCat) delete SLA_DATA[catTeste];
    try{ if(typeof slaCacheLimpar==="function") slaCacheLimpar(); }catch(e){}
  }
  const ok=res.filter(r=>r[1]==="OK").length;
  console.table(res.map(r=>({ caso:r[0], resultado:r[1], detalhe:r[2].join(" · ") })));
  console.log(ok+" de "+res.length+" casos OK");
  window.RESULTADO_ACEITE={ ok:ok, total:res.length, res:res };
  return window.RESULTADO_ACEITE;
})();
