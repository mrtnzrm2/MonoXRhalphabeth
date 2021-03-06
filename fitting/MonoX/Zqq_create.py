import os
import math
from array import array
import optparse
import ROOT
from ROOT import *
import sys

def createHist(trans_h2ddt,tag,filename,sf,lumi,mass,isdata=False):

	massbins = 100;
	masslo   = 0;
	masshi   = 500;

	ptbins = 4;
	ptlo = 175;
	pthi = 775;

	h_pass_ak8 = TH2F(tag+"_pass","; AK8 m_{SD}^{PUPPI} (GeV); AK8 p_{T} (GeV)",massbins,masslo,masshi,ptbins,ptlo,pthi)
	h_fail_ak8 = TH2F(tag+"_fail","; AK8 m_{SD}^{PUPPI} (GeV); AK8 p_{T} (GeV)",massbins,masslo,masshi,ptbins,ptlo,pthi)
	h_pass_matched_ak8 = TH2F(tag+"_pass_matched","; AK8 m_{SD}^{PUPPI} (GeV); AK8 p_{T} (GeV)",massbins,masslo,masshi,ptbins,ptlo,pthi)
	h_pass_unmatched_ak8 = TH2F(tag+"_pass_unmatched","; AK8 m_{SD}^{PUPPI} (GeV); AK8 p_{T} (GeV)",massbins,masslo,masshi,ptbins,ptlo,pthi)
	h_fail_matched_ak8 = TH2F(tag+"_fail_matched","; AK8 m_{SD}^{PUPPI} (GeV); AK8 p_{T} (GeV)",massbins,masslo,masshi,ptbins,ptlo,pthi)
	h_fail_unmatched_ak8 = TH2F(tag+"_fail_unmatched","; AK8 m_{SD}^{PUPPI} (GeV); AK8 p_{T} (GeV)",massbins,masslo,masshi,ptbins,ptlo,pthi)
	
	# validation
	h_pass_msd_ak8 = TH1F(tag+"pass_msd", "; AK8 m_{SD}^{PUPPI}; N", 60, 0, 300)
	h_fail_msd_ak8 = TH1F(tag+"fail_msd", "; AK8 m_{SD}^{PUPPI}; N", 60, 0, 300)
	h_pass_msd_matched_ak8 = TH1F(tag+"pass_msd_matched", "; AK8 m_{SD}^{PUPPI}; N", 60, 0, 300)
	h_pass_msd_unmatched_ak8 = TH1F(tag+"pass_msd_unmatched", "; AK8 m_{SD}^{PUPPI}; N", 60, 0, 300)
	h_fail_msd_matched_ak8 = TH1F(tag+"fail_msd_matched", "; AK8 m_{SD}^{PUPPI}; N", 60, 0, 300)
	h_fail_msd_unmatched_ak8 = TH1F(tag+"fail_msd_unmatched", "; AK8 m_{SD}^{PUPPI}; N", 60, 0, 300)

	print filename+".root"
	infile=ROOT.TFile(filename+".root")	

	tree= infile.Get("Events")
	nent = tree.GetEntries();

	for i in range(tree.GetEntries()):

		if i % sf != 0: 
			continue
		
		tree.GetEntry(i)
		if(i % (1 * nent/100) == 0):
			sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done")
			sys.stdout.flush()

		puweight = tree.puWeight
		fbweight = tree.scale1fb * lumi
		weight = puweight*fbweight*sf
		if isdata: weight = puweight*fbweight

		jmsd_8 = tree.AK8Puppijet0_msd
		
		PT = tree.AK8Puppijet0_pt
		if not PT > 0.: 
			continue
		if jmsd_8 <= 0: jmsd_8 = 0.01

		RHO = math.log(jmsd_8*jmsd_8/PT/PT)

		if RHO < -8.5 or RHO > -1.5: 
			continue

		jtN2b1sd_8 = tree.AK8Puppijet0_N2sdb1
		cur_rho_index = trans_h2ddt.GetXaxis().FindBin(RHO);
		cur_pt_index  = trans_h2ddt.GetYaxis().FindBin(PT);
		if RHO > trans_h2ddt.GetXaxis().GetBinUpEdge( trans_h2ddt.GetXaxis().GetNbins() ): cur_rho_index = trans_h2ddt.GetXaxis().GetNbins();
		if RHO < trans_h2ddt.GetXaxis().GetBinLowEdge( 1 ): cur_rho_index = 1;
		if PT > trans_h2ddt.GetYaxis().GetBinUpEdge( trans_h2ddt.GetYaxis().GetNbins() ): cur_pt_index = trans_h2ddt.GetYaxis().GetNbins();
		if PT < trans_h2ddt.GetYaxis().GetBinLowEdge( 1 ): cur_pt_index = 1;

		DDT = jtN2b1sd_8 - trans_h2ddt.GetBinContent(cur_rho_index,cur_pt_index);

		# non resonant case
		jphi  = 9999;
		dphi  = 9999;
		dpt   = 9999;
		dmass = 9999;
		if mass > 0:
			jphi = getattr(tree,"AK8Puppijet0_phi");
			dphi = math.fabs(tree.genVPhi - jphi)
			dpt = math.fabs(tree.genVPt - PT)/tree.genVPt
			dmass = math.fabs(mass - jmsd_8)/mass
		
		# Lepton, photon veto and tight jets
		if tree.neleLoose == 0 and tree.nmuLoose == 0 and tree.ntau==0 and tree.AK8Puppijet0_isTightVJet ==1:

			# pass category		
			if tree.AK8Puppijet0_N2sdb1 > 0. and PT > 175. and PT < 775.:
				if DDT < 0:
					h_pass_ak8.Fill( jmsd_8, PT, weight )
					## for signal morphing
					h_pass_msd_ak8.Fill( jmsd_8, weight );
					if dphi < 0.8 and dpt < 0.5 and dmass < 0.3:
						h_pass_msd_matched_ak8.Fill( jmsd_8, weight );
						h_pass_matched_ak8.Fill( jmsd_8, PT, weight );
					else:
						h_pass_msd_unmatched_ak8.Fill( jmsd_8, weight );
						h_pass_unmatched_ak8.Fill( jmsd_8, PT, weight );
				# fail category
				if DDT > 0:
					h_fail_ak8.Fill( jmsd_8, PT, weight )
					## for signal morphing
					h_fail_msd_ak8.Fill( jmsd_8, weight );
					if dphi < 0.8 and dpt < 0.5 and dmass < 0.3:
						h_fail_msd_matched_ak8.Fill( jmsd_8, weight );
						h_fail_matched_ak8.Fill( jmsd_8, PT, weight );
					else:
						h_fail_msd_unmatched_ak8.Fill( jmsd_8, weight );	
						h_fail_unmatched_ak8.Fill( jmsd_8, PT, weight );

	hists_out = [];
	#2d histograms
	hists_out.append( h_pass_ak8 );
	hists_out.append( h_fail_ak8 );
	hists_out.append( h_pass_matched_ak8 );
	hists_out.append( h_pass_unmatched_ak8 );
	hists_out.append( h_fail_matched_ak8 );
	hists_out.append( h_fail_unmatched_ak8 );
	#1d validation histograms
	hists_out.append( h_pass_msd_ak8 );
	hists_out.append( h_pass_msd_matched_ak8 );
	hists_out.append( h_pass_msd_unmatched_ak8 );
	hists_out.append( h_fail_msd_ak8 );
	hists_out.append( h_fail_msd_matched_ak8 );
	hists_out.append( h_fail_msd_unmatched_ak8 );

	return hists_out

mass=[10,25,50,75,100,125,200]

outfile=TFile("ZGammaTemplates.root", "recreate");

#lumi =36.600
lumi = 2.44
SF_tau21 =1

f_h2ddt = TFile("PhotonDDTs.root");
trans_h2ddt = f_h2ddt.Get("DDT");
trans_h2ddt.SetDirectory(0)
f_h2ddt.Close()

data_hists = createHist(trans_h2ddt,'data_obs','SinglePhotonmvaEV12av3',15,1,0,True)
qcd_hists = createHist(trans_h2ddt,'qcd','NonResBkg',1,lumi,0)
tqq_hists = createHist(trans_h2ddt,'tqq','TTmvaEVv3_1000pb_weighted',1,lumi,0)
wqq_hists = createHist(trans_h2ddt,'wqq','VectorDiJet1Gammamva_M75',1,lumi,75.)
zqq_hists = createHist(trans_h2ddt,'zqq','VectorDiJet1Gammamva_M100',1,lumi,100.)


for m in mass:
	hs_hists = createHist(trans_h2ddt,'zqq%s'%(m),'VectorDiJet1Gammamva_M%s'%(m),1,lumi,m)
	outfile.cd()
	for h in hs_hists: h.Write();

print("Building pass/fail")	
outfile.cd()
for h in data_hists: h.Write();
for h in qcd_hists: h.Write();
for h in tqq_hists: h.Write();
for h in wqq_hists: h.Write();
for h in zqq_hists: h.Write();
outfile.Write()
outfile.Close()

