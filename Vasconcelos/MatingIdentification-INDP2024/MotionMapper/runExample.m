%%example script that will run the code for a set of .avi files that are
%%found in filePath

%Place path to folder containing example .avi files here
filePath = 'C:\Users\HugoMarques\Downloads\LuisaData\MaleCentered';
filePath = 'C:\Users\HugoMarques\Downloads\LuisaData\MaleCenteredAligned';
filePath = 'C:\Users\HugoMarques\Downloads\LuisaData\MaleAlignedVerified';
filePath = 'C:\Users\hgmar\Downloads\LuisaData\MaleAlignedVerified';

%add utilities folder to path
addpath(genpath('.\utilities\'));
addpath(genpath('.\PCA\'));
addpath(genpath('.\segmentation_alignment\'));
addpath(genpath('.\t_sne\'));
addpath(genpath('.\wavelet\'));

%find all avi files in 'filePath'
imageFiles = findAllImagesInFolders(filePath, 'avi', '\');
%imageFiles{1} = 'C:\Users\HugoMarques\Downloads\LuisaData\MaleCentered\video7_2018-10-09T11_17_09_MaleCentered.avi';
L = length(imageFiles);
numZeros = ceil(log10(L+1e-10));

%define any desired parameter changes here
parameters.samplingFreq = 60;
parameters.trainingSetSize = 3000;

%initialize parameters
parameters = setRunParameters(parameters);
parameters.asymThreshold = 50; % IMPORTANT: For some reason the code breaks if this threshold is too high. It creates alinment files with black frames and this makes the program break at some point
parameters.numProjections = 60;
parameters.pcaModes = 30;
parameters.numModes = 25;
parameters.numProcessors = 12;


firstFrame = 1;
%lastFrame = [];
lastFrame = 54000;

%creating alignment directory
alignmentDirectory = [filePath '\alignment_files\'];

if ~exist(alignmentDirectory,'dir')
    mkdir(alignmentDirectory);
end

alignmentFolders = cell(L,1);

for ii=1:L 
    fileNum = [repmat('0',1,numZeros-length(num2str(ii))) num2str(ii)];
    tempDirectory = [alignmentDirectory 'alignment_' fileNum '/'];
    alignmentFolders{ii} = tempDirectory;
end

%% Run Alignment


%run alignment for all files in the directory
fprintf(1,'Aligning Files\n');

for ii=1:L    
    
    fprintf(1,'\t Aligning File #%4i out of %4i\n',ii,L);
    
    fileNum = [repmat('0',1,numZeros-length(num2str(ii))) num2str(ii)];
    tempDirectory = [alignmentDirectory 'alignment_' fileNum '/'];
    alignmentFolders{ii} = tempDirectory;
    
    outputStruct = runAlignment(imageFiles{ii},tempDirectory,firstFrame,lastFrame,parameters);
    
    save([tempDirectory 'outputStruct.mat'],'outputStruct');
    
    clear outputStruct
    clear fileNum
    clear tempDirectory
    
end


%% Find image subset statistics (a gui will pop-up here)

fprintf(1,'Finding Subset Statistics\n');
numToTest = parameters.pca_batchSize;
[pixels,thetas,means,stDevs,vidObjs] = findRadonPixels(alignmentDirectory,numToTest,parameters);


%% Find postural eigenmodes

fprintf(1,'Finding Postural Eigenmodes\n');
[vecs,vals,meanValues] = findPosturalEigenmodes(vidObjs,pixels,parameters);

vecs = vecs(:,1:parameters.numProjections);

figure
makeMultiComponentPlot_radon_fromVecs(vecs(:,1:15),15,thetas,pixels,[201 90]);
caxis([-3e-3 3e-3])
colorbar
title('First 15 Postural Eigenmodes','fontsize',14,'fontweight','bold');
drawnow;


%% Find projections for each data set

projectionsDirectory = [filePath '.\projections\'];
if ~exist(projectionsDirectory,'dir')
    mkdir(projectionsDirectory);
end

fprintf(1,'Finding Projections\n');
for i=1:L
    
    fprintf(1,'\t Finding Projections for File #%4i out of %4i\n',i,L);
    projections = findProjections(alignmentFolders{i},vecs,meanValues,pixels,parameters);
    
    fileNum = [repmat('0',1,numZeros-length(num2str(i))) num2str(i)];
    fileName = imageFiles{i};
    
    save([projectionsDirectory 'projections_' fileNum '.mat'],'projections','fileName');
    
    clear projections
    clear fileNum
    clear fileName 
    
end


%% Use subsampled t-SNE to find training set 

projectionsDirectory = [filePath, '\projections\'];
fprintf(1,'Finding Training Set\n');
[trainingSetData,trainingSetAmps,projectionFiles] = ...
    runEmbeddingSubSampling(projectionsDirectory,parameters);

%% Run t-SNE on training set


fprintf(1,'Finding t-SNE Embedding for the Training Set\n');
[trainingEmbedding,betas,P,errors] = run_tSne(trainingSetData,parameters);


%% Find Embeddings for each file

fprintf(1,'Finding t-SNE Embedding for each file\n');
embeddingValues = cell(L,1);
for i=1:L
    
    fprintf(1,'\t Finding Embbeddings for File #%4i out of %4i\n',i,L);
    


    load(projectionFiles{i},'projections');
    projections = projections(:,1:parameters.pcaModes);
    
    [embeddingValues{i},~] = ...
        findEmbeddings(projections,trainingSetData,trainingEmbedding,parameters);

    clear projections
    
end

%% Make density plots



maxVal = max(max(abs(combineCells(embeddingValues))));
maxVal = round(maxVal * 1.1);

sigma = maxVal / 40;
numPoints = 501;
rangeVals = [-maxVal maxVal];

[xx,density] = findPointDensity(combineCells(embeddingValues),sigma,numPoints,rangeVals);

densities = zeros(numPoints,numPoints,L);
for i=1:L
    [~,densities(:,:,i)] = findPointDensity(embeddingValues{i},sigma,numPoints,rangeVals);
end


figure
maxDensity = max(density(:));
imagesc(xx,xx,density)
axis equal tight off xy
caxis([0 maxDensity * .8])
colormap(jet)
colorbar

close all

fig = figure

N = ceil(sqrt(L));
M = ceil(L/N);
maxDensity = max(densities(:));
for i=1:L
    subplot(M,N,i)
    imagesc(xx,xx,densities(:,:,i))
    axis equal tight xy
    caxis([0 maxDensity * .8])
    colormap(jet)
    title(['Data Set #' num2str(i)],'fontsize',12,'fontweight','bold');
end



close_parpool

% Post-Process

fpoints = embeddingValues{1};


v = VideoReader([filePath, '\video1_2018-10-08T09_42_47_Tracked.avi']);

% fpoints1 = sum((fpoints-repmat([-62.2, 1.1], size(fpoints,1),1)).^2, 2);
% fpoints2 = sum((fpoints-repmat([-62.2, 1.1], size(fpoints,1),1)).^2, 2);
% 
% [~, ind1] = sort(fpoints1, 'ascend');
% [~, ind2] = sort(fpoints2, 'ascend');

datacursormode('on')

for i=1:10
    figure(fig);
    [x_coord, y_coord] = ginput(1);

    fpoints1 = sum((fpoints-repmat([x_coord, y_coord], size(fpoints,1),1)).^2, 2);
    [~, ind1] = sort(fpoints1, 'ascend');

    figure('Position',[400,400,700,700]);

    shift = 15;
    movsize = 2*shift;

    rndindexes = randperm(100, 9);
    ind1(rndindexes')
    x0 = 3;
    y0 = 3;

    video = [];

        image = [];

        frame = 1;
        icount = 1;
        for x = 1:3
            row = [];
            for y= 1:3
                cim = read(v, [ind1(rndindexes(icount))-30 ind1(rndindexes(icount))+30]);
                row = cat(1,row, squeeze(cim(:,:,1,:)));
                icount = icount + 1;
            end
            
            image = cat(2,image,row);
        
        end

        video = cat(3, video, image);


        for pf = 1:size(video,3)
            
            imshow(video(:,:,pf));
            pause(0.15);
            drawnow
        end
        

        
%         for j=1:9
%             subplot(3,3,j);
%             imshow(imresize(read(v,ind1(j) + vidframe), 0.25));
%             drawnow
%             %imagesc(read(v,ind1(j) + vidframe), "MaxRenderedResolution",128);        
%         end






end







